import test from "node:test";
import assert from "node:assert/strict";
import {
  createBook,
  commitEvent,
  correctEvent,
  projectAccount,
  addSecurity,
  validateImport,
  evaluateAlert,
  priceMetrics,
  annualSummary,
  aggregateBars,
  monitoredIds,
} from "../src/core/engine.mjs";
test("导入触发历史拒绝null和对象展示字段，有效历史记录可恢复", () => {
  const b = createBook();
  const valid = {
    id: "occurrence",
    at: "2026-11-11T10:00:00Z",
    title: "测试提醒",
    instrument: "XSHG:600905",
    value: "10",
  };
  assert.throws(() => validateImport({ ...b, occurrences: [null] }));
  assert.throws(() =>
    validateImport({ ...b, occurrences: [{ ...valid, title: { bad: 1 } }] }),
  );
  assert.equal(
    validateImport({ ...b, occurrences: [valid] }).occurrences.length,
    1,
  );
});
const instrument = {
  id: "XSHG:600905",
  code: "600905",
  name: "三峡能源",
  currency: "CNY",
  market: "A股",
  type: "stock",
  industry: "待分类",
  ownership: "待核实",
};
test("导入拒绝会导致页面异常的对象字段及不安全来源链接", () => {
  const b = addSecurity(createBook(), instrument);
  assert.throws(() =>
    validateImport({ ...b, securities: [{ ...instrument, name: { bad: 1 } }] }),
  );
  assert.throws(() =>
    validateImport({
      ...b,
      calendar: [
        {
          id: "c",
          instrument: instrument.id,
          date: "2026-11-11",
          title: "事件",
          kind: "其他",
          source: "javascript:alert(1)",
          verified: "pending",
          archived: false,
        },
      ],
    }),
  );
});
const event = (
  id,
  type,
  quantity,
  price,
  fee = "0",
  at = "2026-11-11T02:00:00Z",
) => ({
  id,
  account: "main",
  instrument: instrument.id,
  type,
  quantity,
  price,
  fee,
  feeStatus: "known",
  currency: "CNY",
  at,
});
test("正式数据集为空；加入证券幂等，自选不会预填虚构持仓", () => {
  let b = createBook();
  assert.equal(b.events.length, 0);
  b = addSecurity(b, instrument);
  b = addSecurity(b, instrument);
  assert.equal(b.securities.length, 1);
  assert.equal(b.watch.length, 1);
});
test("十进制金额精确，含费买入卖出可独立手算对账", () => {
  let b = addSecurity(createBook(), instrument);
  b = commitEvent(b, event("1", "BUY", "100", "10", "5"));
  b = commitEvent(b, event("2", "BUY", "100", "12", "5"));
  b = commitEvent(b, event("3", "SELL", "50", "13", "5"));
  const p = projectAccount(b).positions[0];
  assert.equal(p.quantity, "150");
  assert.equal(p.cost, "1657.5");
  assert.equal(p.realized, "92.5");
});
test("幂等同键同内容返回原账本，异内容冲突；过期版本拒绝", () => {
  const b = addSecurity(createBook(), instrument),
    e = event("1", "BUY", "3", "0.1");
  const c = commitEvent(b, e);
  assert.deepEqual(commitEvent(c, e), c);
  assert.throws(() => commitEvent(c, { ...e, price: "2" }), /幂等/);
  assert.throws(
    () => commitEvent(c, event("2", "BUY", "1", "1"), b.revision),
    /版本/,
  );
  assert.equal(projectAccount(c).positions[0].cost, "0.3");
});
test("撤销和补录必须回放整个时间线，出现中间负持仓拒绝", () => {
  let b = addSecurity(createBook(), instrument);
  b = commitEvent(b, event("1", "BUY", "100", "10"));
  b = commitEvent(b, event("2", "SELL", "50", "11"));
  assert.throws(() => correctEvent(b, "1", null, "误录"), /负持仓|不足/);
  const c = correctEvent(b, "2", null, "撤销误录");
  assert.equal(projectAccount(c).positions[0].quantity, "100");
  assert.equal(c.events.length, 3);
});
test("分红与未知费用保留完整度，清仓剩余成本归零", () => {
  let b = addSecurity(createBook(), instrument);
  b = commitEvent(b, {
    ...event("1", "BUY", "3", "0.1"),
    feeStatus: "unknown",
  });
  b = commitEvent(b, {
    ...event("d", "DIVIDEND", "0", "0"),
    gross: "3",
    tax: "1",
    net: "2",
  });
  b = commitEvent(b, event("2", "SELL", "3", "0.2"));
  const p = projectAccount(b);
  assert.equal(p.positions[0].cost, "0");
  assert.equal(p.dividends.CNY, "2");
  assert.equal(p.complete, false);
});
test("价格区位与距低点、分位分别计算，缺少完整历史不能冒充三年", () => {
  const m = priceMetrics(
    [
      { date: "2026-11-09", open: 10, high: 20, low: 10, close: 12 },
      { date: "2026-11-10", open: 12, high: 15, low: 11, close: 15 },
    ],
    12,
  );
  assert.equal(m.position, 20);
  assert.equal(m.distanceLow, 20);
  assert.equal(m.percentile, 25);
  assert.equal(m.completeThreeYears, false);
});
test("财报缺失、零与亏损分别统计，ETF不适用", () => {
  const s = annualSummary(
    [
      { year: 2025, profit: "10", revenue: "100", currency: "CNY" },
      { year: 2024, profit: "0" },
      { year: 2023, profit: "-1" },
    ],
    "stock",
  );
  assert.equal(s.positive, 1);
  assert.equal(s.zero, 1);
  assert.equal(s.negative, 1);
  assert.equal(s.missing, 2);
  assert.equal(s.margin, 10);
  assert.equal(annualSummary([], "etf").status, "not_applicable");
});
test("首次满足不是穿越，连续满足不重复，断线后重新建立基线", () => {
  const rule = { id: "r", direction: "below", threshold: 10, cooldown: 0 };
  let r = evaluateAlert(rule, null, 9, 1000);
  assert.equal(r.fired, false);
  r = evaluateAlert(rule, r.state, 11, 2000);
  r = evaluateAlert(rule, r.state, 9, 3000);
  assert.equal(r.fired, true);
  assert.equal(evaluateAlert(rule, r.state, 8, 4000).fired, false);
  assert.equal(evaluateAlert(rule, r.state, 8, 999999).fired, false);
});
test("导入校验拒绝损坏结构、未知引用和非法金额", () => {
  assert.throws(() => validateImport({ version: 2 }), /格式/);
  const b = addSecurity(createBook(), instrument);
  assert.equal(validateImport(JSON.parse(JSON.stringify(b))).version, 2);
  assert.throws(() =>
    validateImport({ ...b, events: [event("x", "BUY", "1", "-1")] }),
  );
});
test("周月年聚合保持真实OHLC与量额，不用插值生成交易日", () => {
  const bars = [
    { date: "2026-10-30", open: 10, high: 13, low: 9, close: 12, volume: 3 },
    { date: "2026-11-02", open: 12, high: 15, low: 11, close: 14, volume: 5 },
  ];
  assert.equal(aggregateBars(bars, "month").length, 2);
  const y = aggregateBars(bars, "year")[0];
  assert.equal(y.open, 10);
  assert.equal(y.close, 14);
  assert.equal(y.high, 15);
  assert.equal(y.low, 9);
  assert.equal(y.volume, 8);
});
test("近五个完整财年不能用更早年份填补中间缺报，缺失不计算为亏损", () => {
  const r = annualSummary(
    [2025, 2023, 2022, 2021, 2020].map((year) => ({ year, profit: "1" })),
    "stock",
    2025,
  );
  assert.equal(r.positive, 4);
  assert.equal(r.missing, 1);
  assert.equal(
    r.reports.some((x) => x.year === 2020),
    false,
  );
});
test("导入拒绝跨账户更正、非法设置与伪造审计类型", () => {
  const b = commitEvent(
    addSecurity(createBook(), instrument),
    event("a", "BUY", "1", "10"),
  );
  b.accounts.push({ id: "other", name: "第二账户", currency: "CNY" });
  assert.throws(() =>
    validateImport({ ...b, settings: { ...b.settings, interval: -1 } }),
  );
  assert.throws(() =>
    validateImport({
      ...b,
      events: [
        ...b.events,
        {
          id: "r",
          type: "REVISION",
          target: "a",
          reason: "篡改",
          at: "2026-11-11T03:00:00Z",
          replacement: { ...event("a", "BUY", "1", "10"), account: "other" },
        },
      ],
    }),
  );
  assert.throws(() =>
    validateImport({
      ...b,
      events: [
        ...b.events,
        { id: "r", type: "REVISION", target: "a", replacement: null },
      ],
    }),
  );
});
test("同一时间的买卖更正保留原事件先后，不能按更正录入时间重排", () => {
  let b = addSecurity(createBook(), instrument);
  b = commitEvent(b, event("buy-tie", "BUY", "100", "10"));
  b = commitEvent(b, event("sell-tie", "SELL", "50", "12"));
  const revised = correctEvent(
    b,
    "buy-tie",
    { ...event("buy-tie", "BUY", "100", "11") },
    "修正原始成交价",
  );
  const p = projectAccount(revised).positions[0];
  assert.equal(p.quantity, "50");
  assert.equal(p.cost, "550");
  assert.equal(p.realized, "50");
});
test("导入提醒的展示字段必须是字符串，避免对象作为页面文本", () => {
  const b = addSecurity(createBook(), instrument);
  assert.throws(() =>
    validateImport({
      ...b,
      alerts: [
        {
          id: "x",
          title: { invalid: true },
          instrument: instrument.id,
          threshold: 10,
          direction: "below",
          cooldown: 60,
          enabled: true,
        },
      ],
    }),
  );
});
test("删除自选后无持仓或提醒不继续轮询，持仓和当前研究标的仍被监控", () => {
  let b = addSecurity(createBook(), instrument);
  assert.deepEqual(monitoredIds(b), [instrument.id]);
  b = { ...b, watch: [] };
  assert.deepEqual(monitoredIds(b), []);
  b = commitEvent(b, event("monitor", "OPENING", "100", "10"));
  assert.deepEqual(monitoredIds(b), [instrument.id]);
  b = commitEvent(b, event("clear-monitor", "SELL", "100", "10"));
  assert.deepEqual(monitoredIds(b), []);
  assert.deepEqual(monitoredIds(b, { researchId: instrument.id }), [
    instrument.id,
  ]);
});
