import test from "node:test";
import assert from "node:assert/strict";
import { loadResearchPacket } from "../src/core/research-packet.mjs";

test('历史请求按自然年稳定分段，展示仍严格保留三年且过期来源明确提示', async () => {
  const calls = [];
  const result = await loadResearchPacket({ id: 'XSHG:600905', type: 'stock' }, {
    asOf: '2026-11-12', signal: new AbortController().signal,
    request: async path => {
      calls.push(path);
      if (path.startsWith('financials')) return { reports: [], cache: { stale: true, fetchedAt: '2026-11-01T00:00:00Z', warning: '财报旧数据' } };
      return { bars: [{ date: '2023-01-01' }, { date: '2023-11-12' }, { date: '2026-11-13' }], cache: { layer: 'd1', stale: false } };
    },
  });
  assert.ok(calls.some(p => p.includes('from=2023-01-01&to=2023-12-31')));
  assert.ok(calls.some(p => p.includes('from=2026-01-01&to=2026-11-12')));
  assert.deepEqual(result.bars.map(b => b.date), ['2023-11-12']);
  assert.ok(result.errors.includes('财报旧数据'));
  assert.equal(result.cacheInfo.length, 5);
});
test("关闭弹窗取消历史读取后，不再请求旧证券财报", async () => {
  const controller = new AbortController(),
    calls = [],
    pending = [];
  const request = (path, { signal }) => {
    calls.push({ path, signal });
    return new Promise((resolve) => pending.push(resolve));
  };
  const task = loadResearchPacket(
    { id: "XSHG:600905", type: "stock" },
    { request, asOf: "2026-11-11", signal: controller.signal },
  );
  assert.ok(calls.length >= 3);
  controller.abort();
  for (const done of pending) done({ bars: [] });
  assert.equal(await task, null);
  assert.equal(
    calls.some((c) => c.path.startsWith("financials/")),
    false,
  );
  assert.ok(calls.every((c) => c.signal.aborted));
});
test("部分历史失败仍保留成功数据并列出缺项，ETF不请求公司财报", async () => {
  let finance = 0;
  const result = await loadResearchPacket(
    { id: "XSHG:588080", type: "etf" },
    {
      request: async (path) => {
        if (path.startsWith("financials/")) finance++;
        if (path.includes("from=2023")) throw Error("首段缺失");
        return {
          bars: [
            { date: "2026-11-10", close: 1, low: 0.9, high: 1.1, open: 1 },
          ],
        };
      },
      asOf: "2026-11-11",
      signal: new AbortController().signal,
    },
  );
  assert.equal(finance, 0);
  assert.equal(result.bars.length, 1);
  assert.equal(result.errors.length, 1);
});
