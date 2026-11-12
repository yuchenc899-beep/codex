export function annualProfitSeries(
  reports,
  endYear = new Date().getUTCFullYear() - 1,
) {
  const valid = reports
    .filter(
      (r) =>
        Number.isInteger(r.year) && r.year <= endYear && r.year > endYear - 5,
    )
    .sort((a, b) => b.year - a.year);
  const currency =
    valid.find((r) => ["CNY", "HKD", "USD"].includes(r.currency))?.currency ||
    null;
  const map = new Map(valid.map((r) => [r.year, r]));
  const rows = Array.from({ length: 5 }, (_, i) => {
    const year = endYear - 4 + i,
      r = map.get(year),
      raw = r?.profit;
    const known =
      raw != null && String(raw).trim() !== "" && Number.isFinite(Number(raw));
    const same = currency && r?.currency === currency;
    const profit = known && same ? Number(raw) : null;
    const prev = map.get(year - 1);
    const prevKnown =
      prev?.profit != null &&
      String(prev.profit).trim() !== "" &&
      Number.isFinite(Number(prev.profit)) &&
      prev.currency === currency;
    return {
      year,
      profit,
      value: profit == null ? null : profit / 1e8,
      currency,
      status: !known
        ? "missing"
        : !same
          ? "currency_mismatch"
          : profit === 0
            ? "zero"
            : profit > 0
              ? "profit"
              : "loss",
      yoy:
        profit != null && prevKnown && Number(prev.profit) > 0
          ? (profit / Number(prev.profit) - 1) * 100
          : null,
    };
  });
  return {
    currency,
    rows,
    unit:
      currency === "HKD"
        ? "亿港元"
        : currency === "USD"
          ? "亿美元"
          : currency === "CNY"
            ? "亿元"
            : "币种待核实",
  };
}
