import { priceMetrics, annualSummary } from "./engine.mjs";
const number = (v) =>
  v == null || String(v).trim() === "" || !Number.isFinite(Number(v))
    ? null
    : Number(v);
const missing = (v) =>
  v == null || v === "" || (typeof v === "number" && !Number.isFinite(v));
const rowCache = new Map();
export function sortRows(rows, key, direction = "asc") {
  return rows
    .map((row, index) => ({ row, index }))
    .sort((a, b) => {
      const x = a.row[key],
        y = b.row[key];
      if (missing(x) || missing(y))
        return missing(x) && missing(y)
          ? String(a.row.id).localeCompare(String(b.row.id)) ||
              a.index - b.index
          : missing(x)
            ? 1
            : -1;
      const cmp =
        typeof x === "number" && typeof y === "number"
          ? x - y
          : String(x).localeCompare(String(y), "zh-CN", { numeric: true });
      return (
        (direction === "desc" ? -cmp : cmp) ||
        String(a.row.id).localeCompare(String(b.row.id)) ||
        a.index - b.index
      );
    })
    .map((x) => x.row);
}
export function filterSecurities(rows, f = {}) {
  const min =
      f.minPrice == null || String(f.minPrice).trim() === ""
        ? null
        : number(f.minPrice),
    max =
      f.maxPrice == null || String(f.maxPrice).trim() === ""
        ? null
        : number(f.maxPrice);
  if (
    (f.minPrice != null && String(f.minPrice).trim() !== "" && min == null) ||
    (f.maxPrice != null && String(f.maxPrice).trim() !== "" && max == null) ||
    (min != null && min < 0) ||
    (max != null && max < 0) ||
    (min != null && max != null && min > max)
  )
    return [];
  const search = (f.search || "").trim().toLocaleLowerCase();
  return rows.filter((r) => {
    if (
      search &&
      !`${r.name} ${r.code || ""} ${r.id} ${r.industry || ""}`
        .toLocaleLowerCase()
        .includes(search)
    )
      return false;
    if (
      f.industry &&
      f.industry !== "all" &&
      f.industry !== "全部行业" &&
      r.industry !== f.industry
    )
      return false;
    if (f.market && f.market !== "all" && r.market !== f.market) return false;
    if (f.type && f.type !== "all" && r.type !== f.type) return false;
    if (
      f.group &&
      f.group !== "all" &&
      f.group !== "全部分组" &&
      !r.groupList?.includes(f.group)
    )
      return false;
    if (f.ownership && f.ownership !== "all" && r.ownership !== f.ownership)
      return false;
    if (
      (min != null || max != null) &&
      (r.price == null ||
        (min != null && r.price < min) ||
        (max != null && r.price > max))
    )
      return false;
    if (f.low20 && !(r.currency === "CNY" && r.price != null && r.price < 20))
      return false;
    if (f.profit && f.profit !== "all") {
      if (r.type !== "stock" && f.profit !== "na") return false;
      if (r.type === "stock" && f.profit === "na") return false;
      if (
        (f.profit === "positive" && !(r.profit != null && r.profit > 0)) ||
        (f.profit === "loss" && !(r.profit != null && r.profit < 0)) ||
        (f.profit === "zero" && r.profit !== 0) ||
        (f.profit === "five-positive" &&
          !(r.profitPositiveYears === 5 && r.profitMissing === 0)) ||
        (f.profit === "missing" && r.profit != null) ||
        (f.profit === "incomplete" && !(r.profitMissing > 0))
      )
        return false;
    }
    const d = r.distanceLow;
    if (
      (f.distance === "below-low" && !(d != null && d < 0)) ||
      (f.distance === "within5" && !(d != null && d >= 0 && d <= 5)) ||
      (f.distance === "within15" && !(d != null && d >= 0 && d <= 15)) ||
      (f.distance === "above15" && !(d != null && d > 15)) ||
      (f.distance === "missing" && d != null)
    )
      return false;
    if (
      (f.data === "loaded" && !r.historyRows) ||
      (f.data === "missing" && r.historyRows > 0) ||
      (f.data === "quote-missing" && r.price != null)
    )
      return false;
    const pnl = r.floating;
    if (
      (f.pnl === "profit" && !(pnl != null && pnl > 0)) ||
      (f.pnl === "loss" && !(pnl != null && pnl < 0)) ||
      (f.pnl === "flat" && pnl !== 0) ||
      (f.pnl === "missing" && pnl != null)
    )
      return false;
    return true;
  });
}
export function buildSecurityRow(
  security,
  quote,
  packet,
  window = "3",
  asOf = new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Shanghai" }),
) {
  const cacheKey = security.id + "|" + window + "|" + asOf,
    quoteKey = JSON.stringify([
      quote?.last,
      quote?.change,
      quote?.pe,
      quote?.sourceTime,
    ]);
  const cached = rowCache.get(cacheKey);
  if (
    cached?.security === security &&
    cached?.packet === packet &&
    cached?.quoteKey === quoteKey
  )
    return cached.row;
  const endYear = Number(asOf.slice(0, 4)) - 1;
  const from = new Date(asOf + "T00:00:00Z");
  if (window === "52w") from.setUTCDate(from.getUTCDate() - 364);
  else from.setUTCFullYear(from.getUTCFullYear() - Number(window || 3));
  const fromDate = from.toISOString().slice(0, 10);
  const bars = (packet?.bars || []).filter(
    (b) => b.date >= fromDate && b.date <= asOf,
  );
  const price = number(quote?.last),
    metrics = priceMetrics(
      bars,
      price > 0 ? price : NaN,
      window === "52w" ? 1 : Number(window || 3),
      asOf,
    ),
    annual = annualSummary(packet?.reports || [], security.type, endYear);
  const latest = (packet?.reports || []).find((r) => r.year === endYear);
  const profit = security.type === "stock" ? number(latest?.profit) : null;
  const row = {
    ...security,
    industry: security.industry || "待分类",
    price: price > 0 ? price : null,
    change: number(quote?.change),
    pe: security.type === "stock" ? number(quote?.pe) : null,
    quoteTime: quote?.sourceTime ? Date.parse(quote.sourceTime) : null,
    historyLow: metrics.low ?? null,
    historyHigh: metrics.high ?? null,
    historyLowDate: metrics.lowDate ?? null,
    distanceLow: metrics.distanceLow,
    position: metrics.position,
    historyRows: metrics.rows,
    historyFrom: metrics.from ?? null,
    historyTo: metrics.to ?? null,
    profit,
    profitCurrency: latest?.currency || null,
    profitYear: endYear,
    profitPositiveYears:
      security.type === "stock" && packet ? annual.positive : null,
    profitMissing: annual.missing,
    annual,
    metrics,
    dataState:
      price == null
        ? "报价缺失"
        : !packet
          ? "资料待加载"
          : !metrics.rows
            ? "历史缺失"
            : packet.errors?.length
              ? "资料部分缺失"
              : "已取得区间资料",
  };
  if (rowCache.size >= 1500) rowCache.delete(rowCache.keys().next().value);
  rowCache.set(cacheKey, { security, packet, quoteKey, row });
  return row;
}
