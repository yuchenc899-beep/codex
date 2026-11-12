# Public Data Cache Implementation Plan

**Goal:** Reopening the dashboard reuses public historical and financial data; private portfolios remain session-only.

**Architecture:** A route-whitelisted Worker cache reads indexed D1 response documents before contacting public providers. Validated complete history chunks and financial reports are the only durable records. Realtime quote and valuation requests bypass D1. Browser HTTP caching complements the database; no scheduled background work or paid subscription is configured.

**Tech Stack:** React, Fetch API, Cloudflare Workers and D1, node:test.

## Policy and limits

- History 1d: calendar-year chunks, completed years 7 days fresh; ranges including today 5 minutes fresh; past ranges ending within 7 days 1 hour. Keep expired successes up to 30 days for source-error fallback, marked stale. Frontend retains exact three-year display cutoff.
- Financials: 6 hours fresh, 30 days maximum fallback. Empty, rejected, malformed or unsupported responses cannot replace a previous success.
- Quotes/valuation: current 5-second short memory cache, no D1 and no browser persistent cache. Intraday remains existing 15-second memory TTL.
- Browser cache-control: historical 1 hour, current-year 60 seconds, financials 10 minutes, no browser stale-if-error directive. Manual reload requests bypass browser freshness; server staleness metadata remains explicit.
- D1 key includes schema, route, security identity, interval, dates, adjustment policy and provider version. Queries use the primary key; maximum persisted body 500 KB, maximum 30 days since retrieval; periodically delete expired documents only during traffic.
- Stale-if-error is implemented in code, not Cache API directives. Original provider timestamps and retrievedAt are preserved; a cached response is never labelled a newly fetched market observation.
- D1 denial/quota/outage falls back to source; unavailable data is explicit. No personal costs, quantities, notes, account records, instrument search terms or quote POST body are stored.
- Scope deliberately excludes per-bar incremental merge: fetching a whole expired year avoids merging adjusted and unadjusted histories. Calendar chunks eliminate moving three-year cache keys; corrections are rechecked, not cached forever.

## Task 1 — Cache policy and failure tests

Create `prototype/server/public-cache.mjs` and tests in `prototype/tests/public-cache.test.mjs`. First demonstrate failures for policies, keyed reads across wrapper instances, TTL expiry, errors, private routes, malformed/empty data, stale markings, concurrency and DB outage. Run `node --test tests/public-cache.test.mjs` red then green.

## Task 2 — Worker and schema

Create idempotent `prototype/migrations/0001_public_cache.sql`; integrate `PUBLIC_DATA` binding in worker and config. Cache wrapper receives a gateway function; gateway memory caching is disabled for persistent routes so an expired D1 lookup really rechecks the source. Add a hard retention cutoff and bounded opportunistic cleanup.

## Task 3 — Stable research ranges and freshness

Change research-packet ranges to calendar years, filter exactly to requested three years. Preserve explicit stale messages in packet errors. Current-day research memory TTL is 5 minutes and financial error packets retry earlier. Show cache policy and stale metadata in UI.

## Task 4 — Verify and publish

Run all node tests, build and Wrangler dry-run. Reuse or create one D1, apply SQL remotely, deploy existing Worker. Probe a public history and finance sample twice and verify source then D1 hit with identical retrievedAt; verify quote route still updates. Record evidence without user securities lists or tokens. No git commit/PR because workspace is not an active Git checkout.
