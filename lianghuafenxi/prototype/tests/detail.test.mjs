import test from "node:test";
import assert from "node:assert/strict";
import { annualProfitSeries } from "../src/core/detail.mjs";
import { parseValuation } from "../server/gateway.mjs";
test("五年利润固定财年，缺失与零分别保留，负基数不计算常规同比", () => {
  const s = annualProfitSeries(
    [
      { year: 2025, profit: "200000000", currency: "CNY" },
      { year: 2024, profit: "0", currency: "CNY" },
      { year: 2023, profit: "-100000000", currency: "CNY" },
      { year: 2021, profit: "100000000", currency: "CNY" },
    ],
    2025,
  );
  assert.deepEqual(
    s.rows.map((r) => r.year),
    [2021, 2022, 2023, 2024, 2025],
  );
  assert.deepEqual(
    s.rows.map((r) => r.value),
    [1, null, -1, 0, 2],
  );
  assert.equal(s.rows[4].yoy, null);
  assert.equal(s.rows[1].status, "missing");
  assert.equal(s.rows[3].status, "zero");
});
test("利润图不混加不同财报币种，ETF与指数无需生成公司利润", () => {
  const s = annualProfitSeries(
    [
      { year: 2025, profit: "1", currency: "HKD" },
      { year: 2024, profit: "1", currency: "CNY" },
    ],
    2025,
  );
  assert.equal(s.rows[3].value, null);
  assert.equal(s.rows[3].status, "currency_mismatch");
});
test("详情接口估值字段区别于列表接口，成交量市场单位分别处理", () => {
  const p = {
    data: {
      f43: 3.31,
      f47: 1608303,
      f48: 533527161,
      f162: 49.69,
      f163: 25.48,
      f164: 113.89,
      f167: 1.07,
      f116: 94625121970.02,
      f117: 94625121970.02,
      f168: 0.56,
      f50: 0.8,
      f86: 1794389400,
    },
  };
  const a = parseValuation(p, "XSHG:600905");
  assert.equal(a.peDynamic, 49.69);
  assert.equal(a.peStatic, 25.48);
  assert.equal(a.peTTM, 113.89);
  assert.equal(a.pb, 1.07);
  assert.equal(a.volumeUnit, "手");
  assert.equal(a.amount, 533527161);
  assert.equal(parseValuation(p, "XHKG:00762").volumeUnit, "股");
  assert.equal(
    parseValuation(
      { data: { f47: 0, f48: 0, f162: "-", f167: "" } },
      "XSHG:600905",
    ).volume,
    0,
  );
  assert.equal(
    parseValuation({ data: { f47: "-", f48: "-" } }, "XSHG:600905").volume,
    null,
  );
});
