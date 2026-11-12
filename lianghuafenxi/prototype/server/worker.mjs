import { handleRequest } from './gateway.mjs';
import { createPublicCache } from './public-cache.mjs';

let cacheBinding, publicRequest;

// Only the built public assets are uploaded. Personal workspaces stay in the browser.
export default {
  async fetch(request, env) {
    const path = new URL(request.url).pathname;
    if (path === '/api/v1/health') {
      return Response.json({ data: { ok: true, storage: 'session', mode: 'production', realProviders: true, publicDataCache: env.PUBLIC_DATA ? 'd1' : 'unbound' } }, {
        headers: { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' },
      });
    }
    if (path.startsWith('/api/')) {
      if (!publicRequest || cacheBinding !== env.PUBLIC_DATA) {
        cacheBinding = env.PUBLIC_DATA;
        publicRequest = createPublicCache({ db: env.PUBLIC_DATA, origin: r => handleRequest(r, fetch, { persistentCache: true }) });
      }
      return publicRequest(request);
    }
    return env.ASSETS.fetch(request);
  },
};
