import test from 'node:test';
import assert from 'node:assert/strict';
import { cachePolicy, createPublicCache } from '../server/public-cache.mjs';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';

const at = Date.parse('2026-11-12T02:00:00Z');
const req = (path) => new Request('https://example.test/api/v1/' + path);
const history = 'history/XSHG:600905?interval=1d&from=2025-01-01&to=2025-12-31';
const success = () => Response.json({ data: { id: 'XSHG:600905', bars: [{ date: '2025-01-02', open: 1, close: 1, high: 1, low: 1 }], rejected: 0, adjustment: 'qfq' }, meta: { received_at: 'original' } });
function database() {
  const rows = new Map();
  return { rows, prepare(sql) { return { bind(...args) { return {
    first: async () => rows.get(args[0]) || null,
    run: async () => {
      if (sql.startsWith('INSERT')) rows.set(args[0], { body: args[1], fetched_at: args[2], fresh_until: args[3], expires_at: args[4] });
      return { success: true };
    },
  }; } }; } };
}
test('only validated public history and financials enter durable cache', () => {
  assert.ok(cachePolicy(req(history), at));
  assert.equal(cachePolicy(req(history.replace('XSHG:', 'XSHG%3A')), at).key, cachePolicy(req(history), at).key);
  for (const path of ['quotes/batch', 'valuation/XSHG:600905', 'instruments?q=bank', 'ledger', 'history/XSHG:600905?interval=1m', 'history/XSHG:600905?from=2026-02-30&to=2026-03-01', history + '&extra=private', 'financials/XHKG:00762']) assert.equal(cachePolicy(req(path), at), null, path);
  assert.equal(cachePolicy(req(history), at).freshMs, 7 * 86400000);
  assert.equal(cachePolicy(req('financials/XSHG:600905'), at).freshMs, 6 * 3600000);
  assert.equal(cachePolicy(req('history/XSHG:600905?from=2026-01-01&to=2026-11-12'), at).freshMs, 300000);
});
test('D1 survives cache instances; canonical query key and original retrieval time retained', async () => {
  const db = database(); let calls = 0;
  const origin = async () => { calls++; return success(); };
  const a = await (await createPublicCache({ db, origin, now: () => at })(req(history))).json();
  const b = await (await createPublicCache({ db, origin, now: () => at + 1000 })(req('history/XSHG:600905?to=2025-12-31&from=2025-01-01&interval=1d'))).json();
  assert.equal(calls, 1); assert.equal(b.meta.cache.layer, 'd1');
  assert.equal(b.meta.cache.fetchedAt, a.meta.cache.fetchedAt);
  assert.equal(b.meta.received_at, 'original');
});
test('expired success refreshes, failed origin preserves marked stale success, hard expiry refuses fallback', async () => {
  const db = database();
  await createPublicCache({ db, origin: async () => success(), now: () => at })(req(history));
  const fail = async () => Response.json({ error: { message: 'offline' } }, { status: 502 });
  const old = await (await createPublicCache({ db, origin: fail, now: () => at + 8 * 86400000 })(req(history))).json();
  assert.equal(old.meta.cache.stale, true); assert.match(old.meta.cache.warning, /旧数据/);
  assert.equal((await createPublicCache({ db, origin: fail, now: () => at + 31 * 86400000 })(req(history))).status, 502);
});
test('empty history cannot overwrite last good data and must not be cached on cold start', async () => {
  const db = database();
  const empty = async () => Response.json({ data: { bars: [] } });
  await createPublicCache({ db, origin: empty, now: () => at })(req(history));
  assert.equal(db.rows.size, 0);
  await createPublicCache({ db, origin: async () => success(), now: () => at })(req(history));
  const response = await (await createPublicCache({ db, origin: empty, now: () => at + 8 * 86400000 })(req(history))).json();
  assert.equal(response.meta.cache.stale, true); assert.equal(response.data.bars.length, 1);
});
test('database failures fall back to source; quote POST never touches database', async () => {
  const db = { prepare() { throw Error('quota'); } };
  const result = await createPublicCache({ db, origin: async () => success(), now: () => at })(req(history));
  assert.equal(result.status, 200);
  const quote = await createPublicCache({ db, origin: async () => new Response('quote') })(new Request('https://example.test/api/v1/quotes/batch', { method: 'POST', body: '{}' }));
  assert.equal(await quote.text(), 'quote');
});
test('manual refresh bypasses fresh D1 and updates its retrieved time', async () => {
  const db = database(); let calls = 0, time = at;
  const cached = createPublicCache({ db, now: () => time, origin: async () => { calls++; return success(); } });
  await cached(req(history)); time += 1000;
  const force = new Request(req(history), { headers: { 'Cache-Control': 'no-cache' } });
  const data = await (await cached(force)).json();
  assert.equal(calls, 2); assert.equal(data.data.cache.fetchedAt, new Date(time).toISOString());
});
test('migration and cache SQL run against real SQLite with indexed primary-key reads', async () => {
  const sql = new DatabaseSync(':memory:');
  sql.exec(readFileSync(new URL('../migrations/0001_public_cache.sql', import.meta.url), 'utf8'));
  const db = { prepare(query) { return { bind(...args) { return {
    first: async () => sql.prepare(query).get(...args),
    run: async () => sql.prepare(query).run(...args),
  }; } }; } };
  let calls = 0;
  const origin = async () => { calls++; return success(); };
  await createPublicCache({ db, origin, now: () => at })(req(history));
  const b = await (await createPublicCache({ db, origin, now: () => at + 1 })(req(history))).json();
  assert.equal(calls, 1); assert.equal(b.meta.cache.layer, 'd1');
  assert.equal(sql.prepare('SELECT count(*) AS n FROM public_cache').get().n, 1);
  sql.close();
});
test('simultaneous requests share origin work and stale fallbacks are not browser fresh', async () => {
  const db = database(); let calls = 0;
  const cached = createPublicCache({ db, now: () => at, origin: async () => { calls++; await new Promise(r => setTimeout(r, 5)); return success(); } });
  const results = await Promise.all([cached(req(history)), cached(req(history))]);
  assert.equal(calls, 1); assert.equal(await results[0].text(), await results[1].text());
  const stale = await createPublicCache({ db, now: () => at + 8 * 86400000, origin: async () => new Response('', { status: 502 }) })(req(history));
  assert.equal(stale.headers.get('Cache-Control'), 'no-store');
});
