export async function loadResearchPacket(security, { request, asOf, signal }) {
  if (signal.aborted) return null;
  const start = new Date(asOf + "T00:00:00Z");
  start.setUTCFullYear(start.getUTCFullYear() - 3);
  const ranges = [];
  const cutoff = start.toISOString().slice(0, 10);
  for (let year = start.getUTCFullYear(); year <= Number(asOf.slice(0, 4)); year++) {
    ranges.push({ from: `${year}-01-01`, to: `${year}-12-31` < asOf ? `${year}-12-31` : asOf });
  }
  const responses = await Promise.allSettled(
    ranges.map((r) =>
      request(
        `history/${encodeURIComponent(security.id)}?interval=1d&from=${r.from}&to=${r.to}`,
        { signal },
      ),
    ),
  );
  if (signal.aborted) return null;
  const cacheInfo = responses.filter(r => r.status === 'fulfilled' && r.value.cache).map(r => r.value.cache);
  const errors = responses
    .filter((r) => r.status === "rejected")
    .map((r) => r.reason.message);
  const bars = responses
    .filter((r) => r.status === "fulfilled")
    .flatMap((r) => r.value.bars || []);
  let financial = { reports: [] };
  if (security.type === "stock") {
    try {
      financial = await request(
        "financials/" + encodeURIComponent(security.id),
        { signal },
      );
    } catch (e) {
      if (signal.aborted) return null;
      errors.push(e.message);
    }
  }
  if (signal.aborted) return null;
  if (financial.cache) cacheInfo.push(financial.cache);
  for (const info of cacheInfo) if (info.stale) errors.push(info.warning || '当前显示旧资料，请核对来源时间');
  return {
    bars: [...new Map(bars.filter(b => b.date >= cutoff && b.date <= asOf).map((b) => [b.date, b])).values()].sort((a, b) =>
      a.date.localeCompare(b.date),
    ),
    reports: financial.reports || [],
    errors,
    cacheInfo,
    warnings: [...new Set(responses.filter(r => r.status === 'fulfilled' && r.value.warning).map(r => r.value.warning))],
    asOf: new Date().toISOString(),
  };
}
