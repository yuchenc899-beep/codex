import test from "node:test";
import assert from "node:assert/strict";
import { createBook, validateImport } from "../src/core/engine.mjs";
test("同一资料与未变报价复用计算结果，价格改变后距离必须重算", () => {
  const s = { id: "XSHG:600905", name: "样本", type: "stock", currency: "CNY" },
    p = {
      bars: [{ date: "2026-11-10", low: 10, high: 20, open: 12, close: 12 }],
      reports: [],
    };
  const first = buildSecurityRow(
    s,
    { last: "12", change: 1, pe: 10 },
    p,
    "3",
    "2026-11-11",
  );
  assert.equal(
    buildSecurityRow(
      s,
      { last: "12", change: 1, pe: 10 },
      p,
      "3",
      "2026-11-11",
    ),
    first,
  );
  assert.equal(
    buildSecurityRow(s, { last: "13", change: 1, pe: 10 }, p, "3", "2026-11-11")
      .distanceLow,
    30,
  );
});
import {
  filterSecurities,
  sortRows,
  buildSecurityRow,
} from "../src/core/table-query.mjs";
const rows = [
  {
    id: "a",
    name: "银行甲",
    industry: "银行",
    currency: "CNY",
    market: "A股",
    type: "stock",
    price: 10,
    profit: 2,
    profitPositiveYears: 5,
    profitMissing: 0,
    distanceLow: 10,
  },
  {
    id: "b",
    name: "电力乙",
    industry: "电力",
    currency: "HKD",
    market: "港股",
    type: "stock",
    price: 20,
    profit: -1,
    profitPositiveYears: 3,
    profitMissing: 0,
    distanceLow: -5,
  },
  {
    id: "c",
    name: "银行丙",
    industry: "银行",
    currency: "CNY",
    market: "A股",
    type: "stock",
    price: null,
    profit: null,
    profitPositiveYears: 0,
    profitMissing: 5,
    distanceLow: null,
  },
];
test("ETF选择公司盈利不适用后，仍须通过距离和数据条件", () => {
  assert.equal(
    filterSecurities(
      [{ ...rows[0], type: "etf", distanceLow: 90, historyRows: 0 }],
      { profit: "na", distance: "within5", data: "loaded" },
    ).length,
    0,
  );
  assert.equal(
    filterSecurities(
      [{ ...rows[0], type: "etf", distanceLow: 2, historyRows: 700 }],
      { profit: "na", distance: "within5", data: "loaded" },
    ).length,
    1,
  );
});
test("导入拒绝损坏的保存视图筛选和排序对象，旧视图仍兼容", () => {
  const b = createBook(),
    v = { name: "视图", search: "", industry: "all", group: "all", low: false };
  assert.equal(validateImport({ ...b, views: [v] }).views.length, 1);
  assert.throws(() =>
    validateImport({
      ...b,
      views: [{ ...v, filters: { search: { bad: 1 } } }],
    }),
  );
  assert.throws(() =>
    validateImport({
      ...b,
      views: [{ ...v, order: { key: "name", direction: { bad: 1 } } }],
    }),
  );
});
test("价格区间包含边界，0与缺失不同，非法或倒置区间不给出误导结果", () => {
  assert.deepEqual(
    filterSecurities(rows, { minPrice: "10", maxPrice: "20" }).map((r) => r.id),
    ["a", "b"],
  );
  assert.deepEqual(
    filterSecurities(rows, { minPrice: "20", maxPrice: "10" }),
    [],
  );
  assert.deepEqual(filterSecurities(rows, { minPrice: "abc" }), []);
  assert.equal(filterSecurities(rows, {}).length, 3);
});
test("行业、公司盈利、低点距离组合筛选，缺财报不能当亏损，ETF不套公司盈利", () => {
  assert.deepEqual(
    filterSecurities(rows, { industry: "银行", profit: "five-positive" }).map(
      (r) => r.id,
    ),
    ["a"],
  );
  assert.deepEqual(
    filterSecurities(rows, { profit: "loss" }).map((r) => r.id),
    ["b"],
  );
  assert.deepEqual(
    filterSecurities(rows, { profit: "missing" }).map((r) => r.id),
    ["c"],
  );
  assert.deepEqual(
    filterSecurities(rows, { distance: "below-low" }).map((r) => r.id),
    ["b"],
  );
  assert.equal(
    filterSecurities([{ ...rows[0], type: "etf" }], { profit: "positive" })
      .length,
    0,
  );
});
test("数值列按数值排序，双向均将缺失放末尾，相等时按证券ID稳定排序", () => {
  const r = [
    { id: "b", value: 20 },
    { id: "c", value: null },
    { id: "a", value: 3 },
    { id: "d", value: 20 },
  ];
  assert.deepEqual(
    sortRows(r, "value", "asc").map((x) => x.id),
    ["a", "b", "d", "c"],
  );
  assert.deepEqual(
    sortRows(r, "value", "desc").map((x) => x.id),
    ["b", "d", "a", "c"],
  );
  assert.equal(r[0].id, "b");
});
test("历史距离沿用实际返回区间，不伪造缺少的最低价；历史旧报价不用作现价", () => {
  const s = {
    id: "XSHG:600905",
    name: "样本",
    currency: "CNY",
    type: "stock",
    industry: "电力",
    archivedQuote: { price: "100" },
  };
  assert.equal(buildSecurityRow(s, null, null).price, null);
  const r = buildSecurityRow(
    s,
    { last: "12" },
    {
      bars: [{ date: "2026-11-10", open: 10, low: 10, high: 15, close: 12 }],
      reports: [],
      errors: [],
    },
    "3",
    "2026-11-11",
  );
  assert.equal(r.historyLow, 10);
  assert.equal(r.distanceLow, 20);
  assert.equal(r.profit, null);
});
