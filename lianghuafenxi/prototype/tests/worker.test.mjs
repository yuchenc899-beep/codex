import { test } from 'node:test';
import assert from 'node:assert/strict';
import worker from '../server/worker.mjs';

test('cloud worker serves assets and handles API without passing env as fetcher', async () => {
  const env = { ASSETS: { fetch: async () => new Response('app') } };
  assert.equal(await (await worker.fetch(new Request('https://example.test/'), env)).text(), 'app');
  const health = await (await worker.fetch(new Request('https://example.test/api/v1/health'), env)).json();
  assert.equal(health.data.mode, 'production');
  const config = await (await worker.fetch(new Request('https://example.test/api/v1/config'), env)).json();
  assert.equal(config.data.storage, 'session');
  assert.equal(config.data.indices.length, 9);
  assert.equal((await worker.fetch(new Request('https://example.test/api/v1/ledger', { method: 'POST' }), env)).status, 403);
});
