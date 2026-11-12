import test from 'node:test';
import assert from 'node:assert/strict';
import { handleRequest } from '../server/gateway.mjs';

test('行情网关使用 Workers 支持的重定向模式，成功响应继续解析', async () => {
  const response = await handleRequest(new Request('https://example.test/api/v1/instruments?q=600905'), async (_url, options) => {
    if (options.redirect === 'error') throw new TypeError('Invalid redirect value at the edge');
    assert.equal(options.redirect, 'manual');
    return new Response('v_hint="sh~600905~三峡能源";');
  });
  assert.equal(response.status, 200);
  const body = await response.json();
  assert.equal(body.data.items[0].id, 'XSHG:600905');
});

test('来源重定向拒绝处理，不请求 Location 目标', async () => {
  let calls = 0;
  const response = await handleRequest(new Request('https://example.test/api/v1/instruments?q=600905'), async (_url, options) => {
    calls++;
    assert.equal(options.redirect, 'manual');
    return new Response(null, { status: 302, headers: { Location: 'https://other.example/' } });
  });
  assert.equal(response.status, 502);
  assert.equal(calls, 1);
  assert.match((await response.json()).error.message, /重定向.*302/);
});
