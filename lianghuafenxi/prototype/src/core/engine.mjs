import Decimal from "decimal.js";
import { isValidTableFilters, isValidTableOrder } from "./view-schema.mjs";
export function aggregateBars(bars, period = "day") {
  if (period === "day") return bars;
  const groups = new Map();
  for (const b of [...bars].sort((a, b) => a.date.localeCompare(b.date))) {
    let key = b.date.slice(0, period === "year" ? 4 : 7);
    if (period === "week") {
      const d = new Date(b.date + "T00:00:00Z");
      d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7));
      key = d.toISOString().slice(0, 10);
    }
    const old = groups.get(key);
    groups.set(
      key,
      old
        ? {
            ...old,
            high: Math.max(old.high, b.high),
            low: Math.min(old.low, b.low),
            close: b.close,
            volume: (old.volume || 0) + (b.volume || 0),
            amount:
              old.amount == null || b.amount == null
                ? null
                : old.amount + b.amount,
            lastDate: b.date,
          }
        : { ...b, date: key, lastDate: b.date },
    );
  }
  return [...groups.values()];
}
const D = Decimal.clone({ precision: 40, rounding: Decimal.ROUND_HALF_UP });
const num = (v, positive = false) => {
  if (!/^-?\d{1,20}(\.\d{1,10})?$/.test(String(v)))
    throw Error("金额或数量格式不合法");
  const d = new D(v);
  if (positive ? d.lte(0) : d.lt(0)) throw Error("金额或数量超出范围");
  return d;
};
const key = (v) =>
  JSON.stringify(v, (_, x) =>
    x && typeof x === "object" && !Array.isArray(x)
      ? Object.fromEntries(
          Object.entries(x).sort(([a], [b]) => a.localeCompare(b)),
        )
      : x,
  );
const idValid = (id) =>
  /^(XSHG|XSHE):\d{6}$|^XHKG:\d{5}$|^INDEX:(SH000001|SZ399001|SZ399006|SH000300|HSI|HSTECH|SPX|IXIC|DJI)$/.test(
    id,
  );
export const createBook = () => ({
  version: 2,
  revision: 0,
  securities: [],
  watch: [],
  groups: ["默认分组"],
  accounts: [{ id: "main", name: "默认账户", currency: "CNY" }],
  events: [],
  notes: {},
  views: [],
  alerts: [],
  occurrences: [],
  calendar: [],
  settings: {
    interval: 5,
    paused: false,
    rulesEnabled: false,
    redUp: true,
    fx: { HKD: null, USD: null },
    lastMonitoring: null,
  },
});
export function addSecurity(book, security, group = "默认分组") {
  if (
    !idValid(security.id) ||
    typeof security.name !== "string" ||
    !security.name ||
    security.name.length > 80 ||
    !["CNY", "HKD", "USD"].includes(security.currency)
  )
    throw Error("证券身份格式不合法");
  const exists = book.securities.some((s) => s.id === security.id);
  const watch = book.watch.some(
    (w) => w.id === security.id && w.group === group,
  );
  return {
    ...book,
    revision: book.revision + (!exists || !watch ? 1 : 0),
    securities: exists ? book.securities : [...book.securities, security],
    watch: watch ? book.watch : [...book.watch, { id: security.id, group }],
    groups: book.groups.includes(group) ? book.groups : [...book.groups, group],
  };
}
function validateEvent(book, e) {
  if (
    !e?.id ||
    typeof e.id !== "string" ||
    typeof e.at !== "string" ||
    (e.note != null && typeof e.note !== "string") ||
    e.id.length > 150 ||
    !book.accounts.some((a) => a.id === e.account) ||
    !Number.isFinite(Date.parse(e.at))
  )
    throw Error("记录ID、账户或时间格式不合法");
  if (["CASH_IN", "CASH_OUT"].includes(e.type)) {
    num(e.amount, true);
    if (!["CNY", "HKD", "USD"].includes(e.currency)) throw Error("币种不支持");
    return;
  }
  const s = book.securities.find((s) => s.id === e.instrument);
  if (!s || s.type === "index") throw Error("证券不存在或指数不支持持仓");
  if (e.currency !== s.currency) throw Error("币种与证券不一致");
  if (["BUY", "SELL", "OPENING"].includes(e.type)) {
    num(e.quantity, true);
    num(e.price, true);
    num(e.fee ?? "0");
    if (!["known", "unknown"].includes(e.feeStatus))
      throw Error("必须明确费用是否已知");
  } else if (e.type === "DIVIDEND") {
    if (!num(e.gross).minus(num(e.tax)).eq(num(e.net)))
      throw Error("税前分红减税费必须等于净额");
  } else if (e.type === "SPLIT") num(e.ratio, true);
  else if (["TRANSFER_IN", "TRANSFER_OUT"].includes(e.type)) {
    num(e.quantity, true);
    if (e.type === "TRANSFER_IN") num(e.cost);
  } else throw Error("记录类型不支持");
}
function effective(book) {
  const events = new Map();
  book.events.forEach((e, sequence) => {
    if (e.type === "REVISION") {
      const original = book.events.find(
        (x) => x.id === e.target && x.type !== "REVISION",
      );
      if (
        !events.has(e.target) ||
        !original ||
        !e.reason?.trim() ||
        !Number.isFinite(Date.parse(e.at))
      )
        throw Error("更正引用或审计信息不合法");
      if (e.replacement) {
        if (
          e.replacement.id !== e.target ||
          e.replacement.account !== original.account
        )
          throw Error("更正不得改变ID或账户");
        validateEvent(book, e.replacement);
      }
      events.set(
        e.target,
        e.replacement
          ? {
              ...e.replacement,
              id: e.target,
              _sequence: book.events.findIndex((x) => x.id === e.target),
            }
          : null,
      );
    } else {
      validateEvent(book, e);
      if (events.has(e.id)) throw Error("事件ID重复");
      events.set(e.id, { ...e, _sequence: sequence });
    }
  });
  return [...events.values()]
    .filter(Boolean)
    .sort(
      (a, b) =>
        Date.parse(a.at) - Date.parse(b.at) || a._sequence - b._sequence,
    );
}
export function projectAccount(book, account = "main") {
  const positions = new Map(),
    cash = {},
    dividends = {};
  let complete = true;
  const add = (target, currency, value) =>
    (target[currency] = new D(target[currency] || 0).plus(value).toString());
  for (const e of effective(book).filter((e) => e.account === account)) {
    if (["CASH_IN", "CASH_OUT"].includes(e.type)) {
      add(cash, e.currency, new D(e.amount).mul(e.type === "CASH_IN" ? 1 : -1));
      continue;
    }
    const p = positions.get(e.instrument) || {
      id: e.instrument,
      quantity: "0",
      cost: "0",
      realized: "0",
      complete: true,
    };
    let q = new D(p.quantity),
      cost = new D(p.cost),
      realized = new D(p.realized);
    if (["BUY", "OPENING"].includes(e.type)) {
      if (e.type === "OPENING" && q.gt(0)) throw Error("期初不能覆盖已有持仓");
      const out = new D(e.quantity).mul(e.price).plus(e.fee || 0);
      q = q.plus(e.quantity);
      cost = cost.plus(out);
      if (e.type === "BUY") add(cash, e.currency, out.negated());
    } else if (["SELL", "TRANSFER_OUT"].includes(e.type)) {
      if (q.lt(e.quantity))
        throw Error(
          "持仓不足：该记录会使历史时间线出现负持仓，请核对数量和发生时间",
        );
      const release = q.eq(e.quantity) ? cost : cost.mul(e.quantity).div(q);
      cost = cost.minus(release);
      q = q.minus(e.quantity);
      if (e.type === "SELL") {
        const income = new D(e.quantity).mul(e.price).minus(e.fee || 0);
        realized = realized.plus(income.minus(release));
        add(cash, e.currency, income);
      }
    } else if (e.type === "TRANSFER_IN") {
      q = q.plus(e.quantity);
      cost = cost.plus(e.cost);
    } else if (e.type === "SPLIT") {
      if (q.eq(0)) throw Error("没有持仓，无法拆合股");
      q = q.mul(e.ratio);
    } else if (e.type === "DIVIDEND") {
      add(dividends, e.currency, e.net);
      add(cash, e.currency, e.net);
    }
    if (e.feeStatus === "unknown") {
      complete = false;
      p.complete = false;
    }
    positions.set(e.instrument, {
      ...p,
      quantity: q.toString(),
      cost: cost.toString(),
      realized: realized.toString(),
    });
  }
  return { positions: [...positions.values()], cash, dividends, complete };
}
export function commitEvent(book, event, expectedRevision = book.revision) {
  const existing = book.events.find((e) => e.id === event.id);
  if (existing) {
    if (key(existing) !== key(event)) throw Error("幂等键冲突");
    return book;
  }
  if (expectedRevision !== book.revision)
    throw Error("账本版本已变化，请重新核对");
  validateEvent(book, event);
  const next = {
    ...book,
    revision: book.revision + 1,
    events: [...book.events, event],
  };
  for (const a of book.accounts) projectAccount(next, a.id);
  return next;
}
/** @param {any} book @param {{indices?: string[], researchId?: string|null}} [options] */
export function monitoredIds(book, { indices = [], researchId = null } = {}) {
  const ids = new Set([
    ...indices,
    ...book.watch.map((w) => w.id),
    ...book.alerts.filter((a) => a.enabled).map((a) => a.instrument),
  ]);
  for (const a of book.accounts)
    for (const p of projectAccount(book, a.id).positions)
      if (new D(p.quantity).gt(0)) ids.add(p.id);
  if (researchId) ids.add(researchId);
  return [...ids].sort();
}
export function correctEvent(book, target, replacement, reason) {
  const original = book.events.find(
    (e) => e.id === target && e.type !== "REVISION",
  );
  if (!original || !reason?.trim()) throw Error("需要原记录及更正原因");
  const revised = replacement
    ? { ...replacement, id: target, account: original.account }
    : null;
  if (revised) validateEvent(book, revised);
  const next = {
    ...book,
    revision: book.revision + 1,
    events: [
      ...book.events,
      {
        id: crypto.randomUUID(),
        type: "REVISION",
        target,
        replacement: revised,
        reason: reason.trim(),
        at: new Date().toISOString(),
      },
    ],
  };
  for (const a of book.accounts) projectAccount(next, a.id);
  return next;
}
export function validateImport(input) {
  if (
    !input ||
    input.version !== 2 ||
    !Number.isSafeInteger(input.revision) ||
    input.revision < 0 ||
    ![
      "securities",
      "watch",
      "accounts",
      "events",
      "groups",
      "alerts",
      "occurrences",
      "views",
    ].every((k) => Array.isArray(input[k])) ||
    !input.settings ||
    !input.notes
  )
    throw Error("导入格式不正确");
  if (input.events.length > 10000 || input.securities.length > 5000)
    throw Error("文件记录过多");
  if (
    input.occurrences.length > 500 ||
    input.occurrences.some(
      (o) =>
        !o ||
        typeof o.id !== "string" ||
        !o.id ||
        o.id.length > 150 ||
        typeof o.title !== "string" ||
        o.title.length > 200 ||
        typeof o.at !== "string" ||
        !Number.isFinite(Date.parse(o.at)) ||
        !idValid(o.instrument),
    )
  )
    throw Error("提醒触发历史格式不正确");
  for (const o of input.occurrences) num(o.value, true);
  if (
    new Set(input.securities.map((s) => s.id)).size !==
      input.securities.length ||
    new Set(input.events.map((s) => s.id)).size !== input.events.length ||
    new Set(input.accounts.map((s) => s.id)).size !== input.accounts.length ||
    !input.accounts.length
  )
    throw Error("重复ID或缺少账户");
  for (const s of input.securities) addSecurity(createBook(), s);
  if (
    input.securities.some(
      (s) =>
        !["stock", "etf", "index"].includes(s.type) ||
        [
          "code",
          "market",
          "industry",
          "ownership",
          "ownershipEvidence",
          "riskEvidence",
          "majorRisk",
        ].some((k) => s[k] != null && typeof s[k] !== "string"),
    )
  )
    throw Error("证券字段格式不正确");
  if (
    input.calendar != null &&
    (!Array.isArray(input.calendar) ||
      input.calendar.some(
        (e) =>
          !e ||
          typeof e.id !== "string" ||
          typeof e.title !== "string" ||
          typeof e.kind !== "string" ||
          !input.securities.some((s) => s.id === e.instrument) ||
          !/^\d{4}-\d{2}-\d{2}$/.test(e.date) ||
          typeof e.source !== "string" ||
          (e.source && !/^https?:\/\//i.test(e.source)) ||
          typeof e.archived !== "boolean" ||
          !["pending", "confirmed"].includes(e.verified),
      ))
  )
    throw Error("事件备忘格式不正确");
  if (
    input.watch.some(
      (w) =>
        !input.securities.some((s) => s.id === w.id) ||
        !input.groups.includes(w.group),
    )
  )
    throw Error("自选引用不正确");
  if (
    input.alerts.some(
      (a) =>
        typeof a.id !== "string" ||
        typeof a.title !== "string" ||
        typeof a.enabled !== "boolean" ||
        !Number.isFinite(a.cooldown) ||
        a.cooldown < 0 ||
        !input.securities.some((s) => s.id === a.instrument) ||
        !Number.isFinite(a.threshold) ||
        a.threshold <= 0 ||
        !["above", "below"].includes(a.direction),
    )
  )
    throw Error("提醒格式不正确");
  if (
    !Number.isFinite(input.settings.interval) ||
    input.settings.interval < 5 ||
    input.settings.interval > 300 ||
    typeof input.settings.paused !== "boolean" ||
    !input.settings.fx ||
    Object.values(input.settings.fx).some(
      (x) =>
        x != null &&
        (!Number.isFinite(Number(x.rate)) ||
          Number(x.rate) <= 0 ||
          !/^\d{4}-\d{2}-\d{2}$/.test(x.date)),
    )
  )
    throw Error("设置格式不正确");
  if (
    input.accounts.some(
      (a) =>
        typeof a.id !== "string" ||
        !a.id ||
        typeof a.name !== "string" ||
        !a.name ||
        !["CNY", "HKD", "USD"].includes(a.currency),
    )
  )
    throw Error("账户格式不正确");
  if (
    input.views.some(
      (v) =>
        typeof v.name !== "string" ||
        typeof v.search !== "string" ||
        typeof v.industry !== "string" ||
        typeof v.group !== "string" ||
        typeof v.low !== "boolean" ||
        (v.filters != null && !isValidTableFilters(v.filters)) ||
        (v.order != null && !isValidTableOrder(v.order)),
    )
  )
    throw Error("视图格式不正确");
  if (
    input.groups.some((g) => typeof g !== "string" || !g || g.length > 40) ||
    Object.values(input.notes).some(
      (n) => typeof n !== "string" || n.length > 10000,
    )
  )
    throw Error("分组或笔记格式不正确");
  for (const a of input.accounts) projectAccount(input, a.id);
  return structuredClone(input);
}
export function evaluateAlert(rule, previous, value, now = Date.now()) {
  if (!Number.isFinite(value)) return { fired: false, state: previous };
  const met =
    rule.direction === "below"
      ? value <= rule.threshold
      : value >= rule.threshold;
  const gap = !previous || now - previous.at > 60000;
  const fired =
    !gap &&
    !previous.met &&
    met &&
    now - (previous.lastFired || 0) >= (rule.cooldown || 0) * 1000;
  return {
    fired,
    state: {
      value,
      met,
      at: now,
      lastFired: fired ? now : previous?.lastFired || 0,
    },
  };
}
export function priceMetrics(
  bars,
  price,
  years = 3,
  asOf = new Date().toISOString().slice(0, 10),
) {
  const until = new Date(asOf + "T00:00:00Z"),
    start = new Date(until);
  start.setUTCFullYear(start.getUTCFullYear() - years);
  const rows = bars
    .filter(
      (b) =>
        b.date >= start.toISOString().slice(0, 10) &&
        b.date <= asOf &&
        [b.high, b.low, b.close].every((v) => Number.isFinite(v) && v > 0),
    )
    .sort((a, b) => a.date.localeCompare(b.date));
  if (!rows.length)
    return {
      position: null,
      distanceLow: null,
      percentile: null,
      completeThreeYears: false,
      rows: 0,
    };
  const low = Math.min(...rows.map((b) => b.low)),
    high = Math.max(...rows.map((b) => b.high));
  const close = rows.map((b) => b.close);
  const ma = (n) =>
    close.length >= n ? close.slice(-n).reduce((a, b) => a + b, 0) / n : null;
  const ret = (n) =>
    close.length > n && Number.isFinite(price)
      ? (price / close.at(-n - 1) - 1) * 100
      : null;
  const validPrice = Number.isFinite(price) && price > 0;
  return {
    rows: rows.length,
    from: rows[0].date,
    to: rows.at(-1).date,
    low,
    high,
    lowDate: rows.findLast((b) => b.low === low).date,
    highDate: rows.findLast((b) => b.high === high).date,
    position:
      validPrice && high > low ? ((price - low) / (high - low)) * 100 : null,
    distanceLow: validPrice
      ? Number(new D(price).div(low).minus(1).mul(100).toFixed(8))
      : null,
    percentile: validPrice
      ? ((close.filter((v) => v < price).length +
          0.5 * close.filter((v) => v === price).length) /
          close.length) *
        100
      : null,
    completeThreeYears:
      rows[0].date <=
        new Date(start.getTime() + 10 * 86400000).toISOString().slice(0, 10) &&
      rows.length >= years * 200,
    ma20: ma(20),
    ma50: ma(50),
    ma60: ma(60),
    ma200: ma(200),
    return20: ret(20),
    return60: ret(60),
  };
}
export function annualSummary(
  reports,
  type = "stock",
  endYear = new Date().getUTCFullYear() - 1,
) {
  if (["etf", "index"].includes(type))
    return {
      status: "not_applicable",
      positive: 0,
      zero: 0,
      negative: 0,
      missing: 0,
      margin: null,
      reports: [],
    };
  const byYear = new Map(
    reports
      .filter(
        (r) =>
          r.profit != null &&
          Number.isInteger(r.year) &&
          r.year <= endYear &&
          r.year > endYear - 5,
      )
      .map((r) => [r.year, r]),
  );
  const valid = [...byYear.values()]
    .sort((a, b) => b.year - a.year)
    .slice(0, 5);
  let positive = 0,
    zero = 0,
    negative = 0;
  for (const r of valid) {
    const d = new D(r.profit);
    if (d.gt(0)) positive++;
    else if (d.eq(0)) zero++;
    else negative++;
  }
  const latest = valid[0];
  return {
    status: valid.length === 5 ? "valid" : "partial",
    positive,
    zero,
    negative,
    missing: 5 - valid.length,
    margin:
      latest?.revenue && new D(latest.revenue).gt(0)
        ? new D(latest.profit).div(latest.revenue).mul(100).toNumber()
        : null,
    reports: valid,
  };
}
