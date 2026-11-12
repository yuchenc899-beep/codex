CREATE TABLE IF NOT EXISTS public_cache (
  cache_key TEXT PRIMARY KEY,
  body TEXT NOT NULL,
  fetched_at INTEGER NOT NULL,
  fresh_until INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS public_cache_expiry ON public_cache(expires_at);
