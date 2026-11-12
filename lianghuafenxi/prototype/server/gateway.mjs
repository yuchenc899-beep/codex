export const INDEX_LIST = [
  ["SH000001", "上证指数", "sh000001", "1.000001", "CNY"],
  ["SZ399001", "深证成指", "sz399001", "0.399001", "CNY"],
  ["SZ399006", "创业板指", "sz399006", "0.399006", "CNY"],
  ["SH000300", "沪深300", "sh000300", "1.000300", "CNY"],
  ["HSI", "恒生指数", "hkHSI", "100.HSI", "HKD"],
  ["HSTECH", "恒生科技", "hkHSTECH", "100.HSTECH", "HKD"],
  ["SPX", "标普500", "usINX", null, "USD"],
  ["IXIC", "纳斯达克综合", "usIXIC", null, "USD"],
  ["DJI", "道琼斯指数", "usDJI", null, "USD"],
];
export function symbolFor(id) {
  if (/^XSHG:\d{6}$/.test(id)) return "sh" + id.slice(5);
  if (/^XSHE:\d{6}$/.test(id)) return "sz" + id.slice(5);
  if (/^XHKG:\d{5}$/.test(id)) return "hk" + id.slice(5);
  const index = INDEX_LIST.find((x) => "INDEX:" + x[0] === id);
  if (index) return index[2];
  throw Object.assign(Error("证券ID不合法"), {
    status: 400,
    code: "INVALID_INSTRUMENT",
  });
}
const positive = (v) =>
  v !== "" && v != null && Number.isFinite(Number(v)) && Number(v) > 0
    ? String(v)
    : null;
const numeric = (v) =>
  v !== "" && v != null && Number.isFinite(Number(v)) ? Number(v) : null;
function sourceTime(v, id) {
  if (
    (id.startsWith("XHKG:") || id === "INDEX:HSI" || id === "INDEX:HSTECH") &&
    /^\d{4}\/\d{2}\/\d{2} \d{2}:\d{2}:\d{2}$/.test(v)
  )
    return new Date(
      v.replaceAll("/", "-").replace(" ", "T") + "+08:00",
    ).toISOString();
  if (/^\d{14}$/.test(v)) {
    const s = `${v.slice(0, 4)}-${v.slice(4, 6)}-${v.slice(6, 8)}T${v.slice(8, 10)}:${v.slice(10, 12)}:${v.slice(12, 14)}+08:00`;
    return new Date(s).toISOString();
  }
  // 美股字段可能为美国当地时间；没有明确时区时保留原值，不猜夏令时。
  return null;
}
export function parseQuotes(raw, ids, receivedAt = new Date().toISOString()) {
  const rows = new Map(
    [...raw.matchAll(/v_([^=\s]+)="([^"]*)"/g)].map((m) => [
      m[1],
      m[2].split("~"),
    ]),
  );
  return ids.map((id) => {
    const symbol = symbolFor(id),
      p = rows.get(symbol);
    if (!p || p.length < 6)
      return { id, last: null, error: "SOURCE_MISSING", receivedAt };
    const index = INDEX_LIST.find((x) => "INDEX:" + x[0] === id),
      currency = index?.[4] || (id.startsWith("XHKG") ? "HKD" : "CNY");
    return {
      id,
      name: index?.[1] || p[1],
      code: p[2],
      last: positive(p[3]),
      previous: positive(p[4]),
      open: positive(p[5]),
      high: positive(p[33]),
      low: positive(p[34]),
      change: numeric(p[32]),
      changeAmount: numeric(p[31]),
      volume: positive(p[6]),
      volumeUnit: "source_native",
      amount: null,
      pe: numeric(p[39]),
      currency,
      sourceTime: sourceTime(p[30] || "", id),
      sourceTimeRaw: p[30] || null,
      receivedAt,
      provider: "腾讯公开行情",
      quality: positive(p[3]) ? "received" : "invalid",
      unitNote: "成交量保留来源原始单位，尚未核实为股/手，暂不换算",
    };
  });
}
export function parseDaily(payload) {
  const raw = payload?.data?.klines || [];
  let rejected = 0;
  const bars = raw.flatMap((row) => {
    const p = row.split(","),
      v = {
        date: p[0],
        open: +p[1],
        close: +p[2],
        high: +p[3],
        low: +p[4],
        volume: numeric(p[5]),
        amount: numeric(p[6]),
      };
    if (
      !/^\d{4}-\d{2}-\d{2}/.test(v.date) ||
      ![v.open, v.close, v.high, v.low].every(
        (n) => Number.isFinite(n) && n > 0,
      ) ||
      v.high < Math.max(v.open, v.close, v.low) ||
      v.low > Math.min(v.open, v.close, v.high)
    ) {
      rejected++;
      return [];
    }
    return [v];
  });
  return { bars, rejected };
}
export function parseValuation(
  payload,
  id,
  receivedAt = new Date().toISOString(),
) {
  const p = payload?.data || {};
  const nonnegative = (v) => {
    const n = numeric(v);
    return n != null && n >= 0 ? n : null;
  };
  const hk = id.startsWith("XHKG:"),
    index = INDEX_LIST.find((x) => "INDEX:" + x[0] === id);
  const currency = hk ? "HKD" : index?.[4] || "CNY";
  const time = Number(p.f86);
  return {
    id,
    last: numeric(p.f43),
    priceDigits:
      Number.isInteger(p.f59) && p.f59 >= 0 && p.f59 <= 6 ? p.f59 : 2,
    volume: nonnegative(p.f47),
    volumeUnit: hk ? "股" : index ? "来源单位" : "手",
    amount: nonnegative(p.f48),
    currency,
    peDynamic: numeric(p.f162),
    peStatic: numeric(p.f163),
    peTTM: numeric(p.f164),
    pb: numeric(p.f167),
    totalMarketCap: nonnegative(p.f116),
    floatMarketCap: nonnegative(p.f117),
    turnover: numeric(p.f168),
    volumeRatio: numeric(p.f50),
    amplitude: numeric(p.f171),
    provider: "东方财富个股详情",
    sourceTime:
      Number.isFinite(time) && time > 946684800 && time < 4102444800
        ? new Date(time * 1000).toISOString()
        : null,
    receivedAt,
    unitNote: hk
      ? "港股成交量按股；金额及市值为港元。"
      : index
        ? "指数成交量保留来源单位，不与股票手数混用。"
        : "沪深成交量按手；金额及市值为人民币元。",
    peNote:
      "动态PE=f162；静态PE=f163；TTM PE=f164；PB=f167（stock/get接口口径，不套用列表字段映射）",
  };
}
export function parseTencentDaily(payload, id) {
  const symbol = symbolFor(id);
  const rows = payload?.code === 0 && payload.data?.[symbol]?.qfqday;
  if (!Array.isArray(rows) || !rows.length) throw Error('备用历史源未返回匹配证券的前复权日线');
  return parseDaily({ data: { klines: rows.map(row => [...row.slice(0, 6), ''].join(',')) } });
}
const cache = new Map();
let valuationPrimaryRetryAt = 0;
function put(k, v, ttl) {
  if (cache.size > 1000) cache.delete(cache.keys().next().value);
  cache.set(k, { value: v, until: Date.now() + ttl });
  return v;
}
function get(k) {
  const x = cache.get(k);
  return x?.until > Date.now() ? x.value : null;
}
async function remote(url, fetcher, encoding = "utf-8", timeout = 10000) {
  const response = await fetcher(url, {
    redirect: "manual",
    signal: AbortSignal.timeout(timeout),
    headers: {
      "User-Agent": "Yuchen-Research/0.2",
      Accept: "application/json,text/plain,*/*",
    },
  });
  if (response.status >= 300 && response.status < 400) {
    await response.body?.cancel();
    throw Error(`供应商返回重定向HTTP ${response.status}，已拒绝跟随`);
  }
  if (!response.ok) throw Error(`供应商HTTP ${response.status}`);
  const reader = response.body.getReader(),
    chunks = [];
  let size = 0;
  while (true) {
    const part = await reader.read();
    if (part.done) break;
    size += part.value.byteLength;
    if (size > 2500000) {
      await reader.cancel();
      throw Error("供应商响应超过2.5MB限制");
    }
    chunks.push(part.value);
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const c of chunks) {
    bytes.set(c, offset);
    offset += c.length;
  }
  return new TextDecoder(encoding).decode(bytes);
}
const jsonRemote = async (url, fetcher, timeout) =>
  JSON.parse(await remote(url, fetcher, 'utf-8', timeout));

export function parseTencentValuation(raw, id, receivedAt = new Date().toISOString()) {
  const symbol = symbolFor(id);
  const match = [...raw.matchAll(/v_([^=\s]+)="([^"]*)"/g)].find(m => m[1] === symbol);
  const p = match?.[2].split('~');
  if (!p || p[2] !== symbol.replace(/^(sh|sz|hk|us)/, '') || !positive(p[3])) throw Error('备用源未返回匹配证券的有效指标');
  const hk = id.startsWith('XHKG:'), index = id.startsWith('INDEX:');
  const amountParts = (p[35] || '').split('/');
  const nonnegative = v => { const n = numeric(v); return n != null && n >= 0 ? n : null; };
  const cap = v => { const n = nonnegative(v); return n == null ? null : n * 1e8; };
  return {
    id, last: numeric(p[3]), priceDigits: hk ? 3 : 2,
    volume: nonnegative(p[6]), volumeUnit: hk ? '股' : index ? '来源单位' : '手',
    amount: hk ? nonnegative(p[37]) : nonnegative(amountParts[2]),
    currency: hk ? 'HKD' : INDEX_LIST.find(x => 'INDEX:' + x[0] === id)?.[4] || 'CNY',
    peTTM: hk || index ? null : numeric(p[39]), peDynamic: hk || index ? null : numeric(p[52]),
    peStatic: hk || index ? null : numeric(p[53]), peSource: hk ? numeric(p[39]) : null,
    pb: hk || index ? null : numeric(p[46]), totalMarketCap: index ? null : cap(p[45]), floatMarketCap: index ? null : cap(p[44]),
    turnover: hk || index ? null : numeric(p[38]), volumeRatio: hk ? null : numeric(p[49]), amplitude: numeric(p[43]),
    provider: '腾讯公开行情（备用）', sourceTime: sourceTime(p[30] || '', id), sourceTimeRaw: p[30] || null, receivedAt,
    unitNote: hk ? '港股成交量按股、成交额为港元；未核实的估值口径留空。' : index ? '指数成交量保留来源单位。' : '沪深成交量按手；成交额为来源组合字段中的元；市值从亿元换算为元。',
    peNote: hk ? '港股备用PE未区分TTM/动态/静态，仅列来源PE，不套用A股字段。' : '腾讯A股字段39为TTM、52为动态、53为静态；已与东方财富公开样例交叉核对。',
  };
}
const urlFor = (base, params) => {
  const u = new URL(base);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, String(v));
  return u;
};
function secidFor(id) {
  symbolFor(id);
  const i = INDEX_LIST.find((x) => "INDEX:" + x[0] === id);
  if (i) {
    if (!i[3])
      throw Object.assign(Error("该指数历史来源尚未核实"), {
        status: 422,
        code: "SOURCE_UNSUPPORTED",
      });
    return i[3];
  }
  return (
    (id.startsWith("XHKG") ? "116" : id.startsWith("XSHG") ? "1" : "0") +
    "." +
    id.slice(5)
  );
}
export function parseSinaFinance(p, asOf) {
  const data = p?.result?.data,
    reports = [];
  for (const [date, r] of Object.entries(data?.report_list || {})) {
    const d = String(date).replaceAll("-", "");
    if (!d.endsWith("1231") || d.slice(0, 4) >= asOf.slice(0, 4)) continue;
    const fields = Object.fromEntries(
      (r.data || []).map((x) => [x.item_title, x.item_value]),
    );
    const profitItem =
      (r.data || []).find((x) => x.item_field === "NETPARECOMPPROF") ||
      (r.data || []).find((x) =>
        [
          "归属于母公司所有者的净利润",
          "归属于母公司的净利润",
          "归属于母公司股东的净利润",
          "归属于上市公司股东的净利润",
        ].includes(x.item_title),
      );
    const profit = profitItem?.item_value;
    const revenue = fields["营业收入"];
    reports.push({
      year: Number(d.slice(0, 4)),
      fiscalEnd: `${d.slice(0, 4)}-12-31`,
      profit:
        profit == null ||
        String(profit).trim() === "" ||
        !Number.isFinite(Number(profit))
          ? null
          : String(profit),
      revenue:
        revenue == null ||
        String(revenue).trim() === "" ||
        !Number.isFinite(Number(revenue))
          ? null
          : String(revenue),
      currency: r.rCurrency || null,
      disclosedAt: r.publish_date || null,
      provider: "新浪财报",
      profitField: profitItem?.item_title || null,
      unit: "元（来源口径）",
    });
  }
  return reports.sort((a, b) => b.year - a.year).slice(0, 5);
}
export async function handleRequest(request, fetcher = fetch, { persistentCache = false } = {}) {
  const u = new URL(request.url),
    path = u.pathname,
    request_id = crypto.randomUUID();
  const send = (data, status = 200) =>
    Response.json(
      {
        data,
        meta: {
          request_id,
          schema_version: 1,
          received_at: new Date().toISOString(),
        },
      },
      {
        status,
        headers: {
          "Cache-Control": "no-store",
          "X-Content-Type-Options": "nosniff",
        },
      },
    );
  try {
    if (path === "/api/v1/health")
      return send({
        ok: true,
        storage: "session",
        mode: "development",
        realProviders: true,
      });
    if (path === "/api/v1/config")
      return send({
        storage: "session",
        indices: INDEX_LIST.map((x) => ({
          id: "INDEX:" + x[0],
          name: x[1],
          code: x[0],
          market: x[4] === "CNY" ? "A股" : x[4] === "HKD" ? "港股" : "美股",
          currency: x[4],
          type: "index",
          industry: "指数",
          ownership: "不适用",
        })),
        capabilities: {
          quotes: true,
          history: true,
          financials: "A股候选来源，港股待核实",
          fx: "需手动填写有日期的汇率",
        },
      });
    if (/^\/api\/v1\/(accounts|ledger|imports|session)(\/|$)/.test(path))
      return send(
        { error: "FEATURE_DISABLED", message: "会话模式不接受私人台账上传" },
        403,
      );
    if (path === "/api/v1/quotes/batch" && request.method === "POST") {
      const text = await request.text();
      if (text.length > 20000)
        throw Object.assign(Error("请求过大"), { status: 413 });
      let body;
      try {
        body = JSON.parse(text);
      } catch {
        throw Object.assign(Error("请求JSON格式不正确"), { status: 400 });
      }
      const ids = body?.instrument_ids;
      if (
        !Array.isArray(ids) ||
        !ids.length ||
        ids.length > 40 ||
        ids.some((id) => typeof id !== "string")
      )
        throw Object.assign(Error("每批需1至40个证券ID"), { status: 400 });
      ids.forEach(symbolFor);
      const snapshot = new Map(ids.map((id) => [id, get("quote:" + id)]));
      const missing = ids.filter((id) => !snapshot.get(id));
      if (missing.length) {
        const raw = await remote(
          "https://qt.gtimg.cn/q=" + missing.map(symbolFor).join(","),
          fetcher,
          "gb18030",
        );
        for (const q of parseQuotes(raw, missing)) {
          put("quote:" + q.id, q, 5000);
          snapshot.set(q.id, q);
        }
      }
      return send({
        items: ids.map((id) => snapshot.get(id)),
        client_round_id: body.client_round_id || null,
      });
    }
    if (request.method !== "GET")
      return send({ error: "METHOD_NOT_ALLOWED" }, 405);
    if (path === "/api/v1/instruments") {
      const q = (u.searchParams.get("q") || "").trim();
      if (!/^[\p{L}\p{N} ._-]{1,30}$/u.test(q))
        throw Object.assign(Error("请输入证券代码或公司名称"), { status: 400 });
      const raw = await remote(
          urlFor("https://smartbox.gtimg.cn/s3/", { q, t: "all" }),
          fetcher,
          "gb18030",
        ),
        hint = raw.match(/"([^"]*)"/)?.[1] || "";
      const items = hint
        .split("^")
        .flatMap((row) => {
          const p = row.split("~");
          if (!["sh", "sz", "hk"].includes(p[0]) || !/^\d{5,6}$/.test(p[1]))
            return [];
          return [
            {
              id:
                (p[0] === "sh" ? "XSHG" : p[0] === "sz" ? "XSHE" : "XHKG") +
                ":" +
                p[1],
              code: p[1],
              name: p[2].replace(/\\u([0-9a-f]{4})/gi, (_, n) =>
                String.fromCharCode(parseInt(n, 16)),
              ),
              market: p[0] === "hk" ? "港股" : "A股",
              currency: p[0] === "hk" ? "HKD" : "CNY",
              type: /ETF|LOF/i.test(p[2]) ? "etf" : "stock",
              industry: "待分类",
              ownership: "待核实",
              provider: "腾讯证券搜索",
            },
          ];
        })
        .slice(0, 20);
      return send({ items });
    }
    const match = path.match(
      /^\/api\/v1\/(history|financials|valuation)\/(.+)$/,
    );
    if (match) {
      const id = decodeURIComponent(match[2]);
      symbolFor(id);
      const interval = u.searchParams.get("interval") || "1d",
        now = new Date(),
        asOf = now.toISOString().slice(0, 10);
      const ckey = path + "?" + u.searchParams.toString();
      const saved = persistentCache && match[1] !== 'valuation' && interval === '1d' ? null : get(ckey);
      if (saved) return send(saved);
      if (match[1] === "valuation") {
        const secid = secidFor(id);
        let primaryError = '东方财富暂处重试间隔';
        if (Date.now() >= valuationPrimaryRetryAt) {
        try {
        const payload = await jsonRemote(
          urlFor("https://push2.eastmoney.com/api/qt/stock/get", {
            secid,
            fltt: 2,
            invt: 2,
            fields:
              "f43,f47,f48,f50,f57,f58,f59,f86,f116,f117,f162,f163,f164,f167,f168,f171,f172",
          }),
          fetcher,
          4000,
        );
        if (!payload?.data || !positive(payload.data.f43)) throw Error("详情源未返回有效证券指标");
        if (payload.data.f57 && String(payload.data.f57) !== id.split(':')[1]) throw Error('详情源证券代码不匹配');
        return send(put(ckey, parseValuation(payload, id), 5000));
        } catch (e) {
          primaryError = e.message;
          valuationPrimaryRetryAt = Date.now() + 60000;
        }
        }
        const raw = await remote('https://qt.gtimg.cn/q=' + symbolFor(id), fetcher, 'gb18030', 5000);
        const fallback = parseTencentValuation(raw, id);
        fallback.warning = '东方财富不可用（' + primaryError + '），已切换腾讯实时备用源；缺失字段保留为空。';
        return send(put(ckey, fallback, 5000));
      }
      if (match[1] === "financials") {
        if (!id.startsWith("XSHG") && !id.startsWith("XSHE"))
          throw Object.assign(
            Error("港股财报币种及年度来源尚待核实，未填充替代数据"),
            { status: 422, code: "SOURCE_UNSUPPORTED" },
          );
        const payload = await jsonRemote(
          urlFor(
            "https://quotes.sina.cn/cn/api/openapi.php/CompanyFinanceService.getFinanceReport2022",
            {
              paperCode: symbolFor(id),
              source: "lrb",
              type: 0,
              page: 1,
              num: 24,
            },
          ),
          fetcher,
        );
        const reports = parseSinaFinance(payload, asOf);
        return send(
          put(ckey, { id, reports, provider: "新浪财报", asOf }, 3600000),
        );
      }
      const secid = secidFor(id),
        from =
          u.searchParams.get("from") || `${now.getUTCFullYear() - 1}-01-01`,
        to = u.searchParams.get("to") || asOf;
      if (
        !/^\d{4}-\d{2}-\d{2}$/.test(from) ||
        !/^\d{4}-\d{2}-\d{2}$/.test(to) ||
        !Number.isFinite(Date.parse(from)) ||
        !Number.isFinite(Date.parse(to)) ||
        new Date(from).toISOString().slice(0, 10) !== from ||
        new Date(to).toISOString().slice(0, 10) !== to ||
        Date.parse(to) < Date.parse(from) ||
        Date.parse(to) - Date.parse(from) > 370 * 86400000
      )
        throw Object.assign(Error("每批历史范围最多370天"), { status: 400 });
      if (!["1d", "1m"].includes(interval))
        throw Object.assign(Error("周期不支持"), { status: 400 });
      const providerUrl =
        interval === "1m"
          ? urlFor("https://push2his.eastmoney.com/api/qt/stock/trends2/get", {
              secid,
              fields1: "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11",
              fields2: "f51,f52,f53,f54,f55,f56,f57,f58",
              ndays: 1,
              iscr: 0,
              iscca: 0,
            })
          : urlFor("https://push2his.eastmoney.com/api/qt/stock/kline/get", {
              secid,
              fields1: "f1,f2,f3,f4,f5,f6",
              fields2: "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
              klt: 101,
              fqt: 1,
              beg: from.replaceAll("-", ""),
              end: to.replaceAll("-", ""),
            });
      let payload, parsed, historyProvider = '东方财富', warning = null;
      try {
        payload = await jsonRemote(providerUrl, fetcher, interval === '1d' ? 4000 : 10000);
        if (interval === '1d' && !payload?.data?.klines?.length) throw Error('主源未返回日线');
      } catch (e) {
        if (interval !== '1d') throw e;
        const backup = await jsonRemote(urlFor('https://web.ifzq.gtimg.cn/appstock/app/fqkline/get', {
          param: `${symbolFor(id)},day,${from},${to},640,qfq`,
        }), fetcher, 8000);
        parsed = parseTencentDaily(backup, id);
        parsed.bars = parsed.bars.filter(b => b.date >= from && b.date <= to);
        historyProvider = '腾讯前复权日线（备用）';
        warning = '东方财富历史源不可用，已切换腾讯前复权日线；成交额缺失时留空。';
      }
      if (interval === "1m")
        payload.data = { ...payload.data, klines: payload.data?.trends };
      parsed ||= parseDaily(payload);
      return send(
        put(
          ckey,
          {
            id,
            ...parsed,
            provider: historyProvider,
            warning,
            interval,
            adjustment: interval === "1d" ? "qfq" : "none",
            from,
            to,
            asOf,
            coverage: "returned",
            completeSinceIPO: false,
          },
          interval === "1m" ? 15000 : 3600000,
        ),
      );
    }
    return send({ error: "NOT_FOUND" }, 404);
  } catch (e) {
    const status = e.status || 502;
    return Response.json(
      {
        error: {
          code: e.code || (status === 400 ? "INVALID_INPUT" : "PROVIDER_ERROR"),
          message: status === 502 ? "数据源暂不可用：" + e.message : e.message,
          retryable: status >= 500,
        },
        meta: { request_id },
      },
      { status, headers: { "Cache-Control": "no-store" } },
    );
  }
}
export default { fetch: handleRequest };
