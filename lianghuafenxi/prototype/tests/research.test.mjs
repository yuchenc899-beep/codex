import test from "node:test";
import assert from "node:assert/strict";
import { comparePrices, researchAssessment } from "../src/core/research.mjs";
test("基准比较只用共同交易日期，跨市场缺口不补造收益", () => {
  const a = [
      { date: "2026-01-01", close: 10 },
      { date: "2026-01-02", close: 11 },
      { date: "2026-01-03", close: 12 },
    ],
    b = [
      { date: "2026-01-02", close: 20 },
      { date: "2026-01-03", close: 18 },
    ];
  const r = comparePrices(a, b);
  assert.deepEqual(r.dates, ["2026-01-02", "2026-01-03"]);
  assert.equal(r.subject[0], 0);
  assert.ok(Math.abs(r.subject[1] - 9.090909) < 0.00001);
  assert.ok(Math.abs(r.benchmark[1] + 10) < 0.00001);
});
test("规则默认关闭；已知连续亏损优先；风险与历史未核实不自动给买入", () => {
  const p = {
    enabled: false,
    security: { type: "stock" },
    metrics: {
      position: 10,
      distanceLow: 2,
      completeThreeYears: true,
      ma50: 10,
      ma200: 9,
    },
    price: 11,
    annual: {
      status: "valid",
      positive: 5,
      reports: [
        { year: 2025, profit: "10" },
        { year: 2024, profit: "10" },
      ],
    },
  };
  assert.equal(researchAssessment(p).label, "研判规则待启用");
  assert.equal(researchAssessment({ ...p, enabled: true }).label, "资料不足");
  assert.equal(
    researchAssessment({
      ...p,
      enabled: true,
      annual: {
        ...p.annual,
        reports: [
          { year: 2025, profit: "-1" },
          { year: 2024, profit: "-1" },
        ],
      },
    }).label,
    "风险优先",
  );
  assert.equal(
    researchAssessment({ ...p, enabled: true, security: { type: "etf" } })
      .label,
    "规则待配置",
  );
});
