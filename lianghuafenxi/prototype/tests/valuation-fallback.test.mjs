import test from 'node:test';
import assert from 'node:assert/strict';
import { handleRequest, parseTencentValuation } from '../server/gateway.mjs';
function raw(id = 'sh600906') {
  const p = Array(85).fill('');
  Object.assign(p, { 0: '1', 1: 'public sample', 2: id.slice(2), 3: '3.29', 6: '414254', 30: '20261112110420', 35: '3.29/414254/136353209', 38: '0.14', 39: '113.20', 43: '1.21', 44: '940.53', 45: '940.53', 46: '1.06', 49: '0.78', 52: '49.39', 53: '25.32', 82: 'CNY' });
  return `v_${id}="${p.join('~')}";`;
}
test('腾讯A股备用字段不混淆PE口径，金额取精确元，市值亿元换元', () => {
  const m = parseTencentValuation(raw(), 'XSHG:600906');
  assert.equal(m.peTTM, 113.2); assert.equal(m.peDynamic, 49.39); assert.equal(m.peStatic, 25.32);
  assert.equal(m.pb, 1.06); assert.equal(m.volume, 414254); assert.equal(m.volumeUnit, '手');
  assert.equal(m.amount, 136353209); assert.equal(m.totalMarketCap, 94053000000);
  assert.throws(() => parseTencentValuation(raw(), 'XSHG:600907'));
});
test('东方财富失败时使用实时腾讯备用，并明确列出原源失败', async () => {
  const calls = [];
  const response = await handleRequest(new Request('https://test/api/v1/valuation/XSHG:600906'), async url => {
    calls.push(String(url));
    return String(url).includes('eastmoney') ? new Response('', { status: 502 }) : new Response(raw());
  });
  assert.equal(response.status, 200);
  const m = (await response.json()).data;
  assert.match(m.provider, /腾讯/); assert.match(m.warning, /东方财富/);
  assert.equal(calls.length, 2); assert.equal(m.amount, 136353209);
});
test('港股不套用A股估值索引，成交量按股、金额按港元', () => {
  const p = Array(80).fill('');
  Object.assign(p, { 0: '100', 1: 'public HK', 2: '00762', 3: '5.475', 6: '8630018', 30: '2026/11/12 10:48:50', 37: '47544359.360', 39: '7.27', 44: '1675.2473', 45: '1675.2473', 46: 'CHINA UNICOM', 52: '0', 53: '0' });
  const m = parseTencentValuation(`v_hk00762="${p.join('~')}";`, 'XHKG:00762');
  assert.equal(m.volumeUnit, '股'); assert.equal(m.amount, 47544359.36);
  assert.equal(m.peTTM, null); assert.equal(m.peStatic, null); assert.equal(m.peDynamic, null);
  assert.equal(m.pb, null); assert.equal(m.peSource, 7.27);
  assert.equal(m.sourceTime, '2026-11-12T02:48:50.000Z');
});
