export function comparePrices(subject, benchmark) {
  const other = new Map(
    benchmark.filter((b) => b.close > 0).map((b) => [b.date, b.close]),
  );
  const common = subject
    .filter((b) => b.close > 0 && other.has(b.date))
    .sort((a, b) => a.date.localeCompare(b.date));
  if (!common.length) return { dates: [], subject: [], benchmark: [] };
  const first = common[0];
  return {
    dates: common.map((b) => b.date),
    subject: common.map((b) => (b.close / first.close - 1) * 100),
    benchmark: common.map(
      (b) => (other.get(b.date) / other.get(first.date) - 1) * 100,
    ),
  };
}
export function researchAssessment({
  enabled,
  security,
  metrics: m,
  price,
  annual,
  historyErrors = [],
}) {
  const ruleVersion = "research-v0.1-draft";
  const result = (label, reasons, missing = []) => ({
    label,
    reasons,
    missing,
    ruleVersion,
  });
  if (security?.type === "index")
    return result("指数观察", ["展示价格区位和趋势，不套公司盈利规则"]);
  if (!enabled)
    return result("研判规则待启用", [
      "可在设置中启用候选规则试算，规则尚未经投资效果验证",
    ]);
  if (security?.type === "etf")
    return result("规则待配置", ["ETF公司利润规则不适用"]);
  const years = annual.reports?.slice().sort((a, b) => b.year - a.year) || [];
  if (
    security?.majorRisk ||
    (years.length >= 2 &&
      years[0].year === years[1].year + 1 &&
      Number(years[0].profit) < 0 &&
      Number(years[1].profit) < 0)
  )
    return result("风险优先", [
      security.majorRisk || "最近两个已取得的连续完整财年均亏损",
    ]);
  const missing = [];
  if (!Number.isFinite(price) || price <= 0) missing.push("有效现价");
  if (
    !m.completeThreeYears ||
    historyErrors.length ||
    !security.historyReviewed
  )
    missing.push("人工核验可比三年历史");
  if (annual.status !== "valid") missing.push("五个完整财年关键资料");
  if (!security.riskEvidence) missing.push("重大事项核验依据");
  if (missing.length)
    return result("资料不足", ["价格低位本身不能给出买入标签"], missing);
  const latestProfit = Number(years[0]?.profit) > 0;
  const trend = price > m.ma50 && m.ma50 > m.ma200 && m.ma200 > 0;
  if (
    m.position <= 20 &&
    m.distanceLow <= 10 &&
    annual.positive >= 4 &&
    latestProfit &&
    Number(years[1]?.profit) > 0 &&
    trend
  )
    return result("值得考虑买入", [
      "低区位、距低点较近，近两年盈利且中期趋势偏强",
      "仍需结合估值、现金流、负债与个人仓位；此为候选规则试算",
    ]);
  if (m.position <= 30 && m.distanceLow <= 15 && latestProfit)
    return result("重点关注", [
      "低区位且最近财年盈利",
      trend ? "中期趋势偏强" : "趋势尚待确认",
    ]);
  return result("继续观察", ["未满足当前候选规则中的低位与趋势组合条件"]);
}
