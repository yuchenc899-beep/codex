const DAY = 86400000;
const RETENTION = 30 * DAY;
function validDate(s) {
  return /^\d{4}-\d{2}-\d{2}$/.test(s || '') && Number.isFinite(Date.parse(s)) && new Date(s).toISOString().slice(0, 10) === s;
}
export function cachePolicy(request, now = Date.now()) {
  if (request.method !== 'GET') return null;
  const u = new URL(request.url);
  let path;
  try { path = decodeURIComponent(u.pathname); } catch { return null; }
  const m = path.match(/^\/api\/v1\/(history|financials)\/((?:XSHG|XSHE):\d{6}|XHKG:\d{5}|INDEX:[A-Z0-9]+)$/);
  if (!m) return null;
  let freshMs, browserSeconds;
  if (m[1] === 'financials') {
    if (!/^(XSHG|XSHE):/.test(m[2]) || u.search) return null;
    freshMs = 6 * 3600000; browserSeconds = 600;
  } else {
    const allowed = ['interval', 'from', 'to'];
    if ([...u.searchParams.keys()].some(k => !allowed.includes(k) || u.searchParams.getAll(k).length !== 1)) return null;
    if ((u.searchParams.get('interval') || '1d') !== '1d') return null;
    const from = u.searchParams.get('from'), to = u.searchParams.get('to');
    if (!validDate(from) || !validDate(to) || from > to || Date.parse(to) - Date.parse(from) > 370 * DAY) return null;
    const today = new Date(now + 8 * 3600000).toISOString().slice(0, 10);
    if (to > today) return null;
    const recent = Date.parse(today) - Date.parse(to);
    freshMs = recent === 0 ? 300000 : recent <= 7 * DAY ? 3600000 : 7 * DAY;
    browserSeconds = recent === 0 ? 60 : recent <= 7 * DAY ? 300 : 3600;
    u.searchParams.set('interval', '1d');
  }
  u.searchParams.sort();
  return { key: 'public-v1-qfq-em-sina:' + path + u.search, kind: m[1], freshMs, browserSeconds };
}
function usable(body, policy) {
  const d = body?.data;
  if (!d || body.error) return false;
  if (policy.kind === 'history') return Array.isArray(d.bars) && d.bars.length > 0 && !d.rejected && d.adjustment === 'qfq' && d.bars.every(b => validDate(b.date) && ['open', 'close', 'high', 'low'].every(k => Number.isFinite(b[k]) && b[k] > 0));
  return Array.isArray(d.reports) && d.reports.length > 0 && d.reports.every(r => Number.isInteger(r.year) && r.profit != null && Number.isFinite(Number(r.profit)));
}
function decorate(record, policy, now, layer, stale = false, warning = null) {
  const body = JSON.parse(record.body);
  body.meta = { ...body.meta, cache: { layer, stale, fetchedAt: new Date(record.fetched_at).toISOString(), freshUntil: new Date(record.fresh_until).toISOString(), warning } };
  body.data.cache = body.meta.cache;
  const ttl = Math.max(0, Math.min(policy.browserSeconds, Math.floor((record.fresh_until - now) / 1000)));
  return Response.json(body, { headers: { 'Cache-Control': stale || ttl <= 0 ? 'no-store' : `private, max-age=${ttl}`, 'X-Content-Type-Options': 'nosniff', 'X-Data-Cache': layer + (stale ? '-stale' : '') } });
}
export function createPublicCache({ db, origin, now = Date.now }) {
  const inflight = new Map();
  let cleanupAt = 0;
  async function load(request, policy) {
    const time = now();
    let old = null;
    try {
      old = await db?.prepare('SELECT body, fetched_at, fresh_until, expires_at FROM public_cache WHERE cache_key = ?').bind(policy.key).first();
      if (old && (!Number.isFinite(old.fetched_at) || old.expires_at <= time || !usable(JSON.parse(old.body), policy))) old = null;
    } catch { old = null; }
    if (old?.fresh_until > time && !/no-cache|max-age=0/.test(request.headers.get('Cache-Control') || '')) return decorate(old, policy, time, 'd1');
    let response;
    try { response = await origin(request); }
    catch {
      response = Response.json({ error: { message: '数据源请求失败', retryable: true } }, { status: 502 });
    }
    let body;
    if (response.ok) { try { body = await response.clone().json(); } catch {} }
    const serialized = body && JSON.stringify(body);
    if (response.ok && serialized?.length <= 500000 && usable(body, policy)) {
      const record = { body: serialized, fetched_at: time, fresh_until: time + policy.freshMs, expires_at: time + RETENTION };
      let warning = db ? null : '云端数据库尚未连接，本次使用来源数据和浏览器短缓存';
      try {
        if (db) {
          await db.prepare('INSERT INTO public_cache (cache_key, body, fetched_at, fresh_until, expires_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(cache_key) DO UPDATE SET body=excluded.body, fetched_at=excluded.fetched_at, fresh_until=excluded.fresh_until, expires_at=excluded.expires_at').bind(policy.key, record.body, record.fetched_at, record.fresh_until, record.expires_at).run();
          if (time >= cleanupAt) {
            cleanupAt = time + 3600000;
            await db.prepare('DELETE FROM public_cache WHERE cache_key IN (SELECT cache_key FROM public_cache WHERE expires_at <= ? LIMIT 100)').bind(time).run();
          }
        }
      } catch { warning = '云端缓存暂不可用，本次已直接查询数据源'; }
      return decorate(record, policy, now(), 'source', false, warning);
    }
    if (old) return decorate(old, policy, now(), 'd1', true, '数据源更新失败，正在显示旧数据，请核对缓存时间');
    return response;
  }
  return async request => {
    const policy = cachePolicy(request, now());
    if (!policy) return origin(request);
    // Share work only inside this isolate; response clones have independent bodies.
    if (!inflight.has(policy.key)) inflight.set(policy.key, load(request, policy).finally(() => inflight.delete(policy.key)));
    return (await inflight.get(policy.key)).clone();
  };
}
