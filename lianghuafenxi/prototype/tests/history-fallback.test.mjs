import test from 'node:test';
import assert from 'node:assert/strict';
import { handleRequest, parseTencentDaily } from '../server/gateway.mjs';
const payload = { code: 0, data: { sh600905: { qfqday: [['2025-01-02','4.262','4.142','4.272','4.122','1572234']] } } };
test('前复权备用只接受匹配证券的qfqday，不把原价冒充前复权', () => {
  const p = parseTencentDaily(payload, 'XSHG:600905');
  assert.equal(p.bars[0].close, 4.142); assert.equal(p.bars[0].amount, null);
  assert.throws(() => parseTencentDaily({ code: 0, data: { sh600905: { day: payload.data.sh600905.qfqday } } }, 'XSHG:600905'));
  assert.throws(() => parseTencentDaily(payload, 'XSHG:600906'));
});
test('历史主源520时返回腾讯前复权数据，并注明供应商变更', async () => {
  const r = await handleRequest(new Request('https://example.test/api/v1/history/XSHG:600905?interval=1d&from=2025-01-01&to=2025-12-31'), async url => String(url).includes('eastmoney') ? new Response('', { status: 520 }) : Response.json(payload), { persistentCache: true });
  assert.equal(r.status, 200);
  const d = (await r.json()).data;
  assert.equal(d.bars.length, 1); assert.equal(d.adjustment, 'qfq');
  assert.match(d.provider, /腾讯/); assert.match(d.warning, /东方财富/);
});
