# Architecture audit — 2026-11-06

Scope: both reachable commits (`86d05ee`, `f51fc78`), every application Python module,
template, stylesheet, browser script, test and operating document. No application
code was changed before inspection. Baseline: 19/19 unittest integration tests pass.
The repository had no AGENTS.md, .gitignore, CI, migrations or software LICENSE.

## Existing and verified

Flask/Waitress renders Jinja with locally served IBM Plex, semantic theme tokens,
responsive CSS, keyboard controls, reduced motion and server-generated SVG charts.
`app.py` owns routes, authentication, sessions, CSRF, rate limits, news impact windows,
CSV and contextual chat. `collector.py` uses three background threads for Yahoo daily
prices, Nasdaq fallback and Yahoo RSS. `ai.py` bounds DeepSeek context and validates
JSON; credentials are optional. External AI output is rendered as text.

Routes: GET `/`, `/app`, `/symbol/<ticker>`, `/news`, `/learn`, `/api/status`,
`/api/asset/<ticker>`, `/export/<ticker>.csv`, `/health`; GET/POST `/login`, `/register`,
`/watchlist` (authenticated); POST `/logout`, `/api/refresh`,
`/api/analyze/<ticker>` (authenticated); GET/POST/DELETE `/api/chat`.
Legacy APIs return `active`, `asset/prices/news`, `messages`, `answer/sources`,
`analyzed/message` and `started/active/message`, respectively. Writes require CSRF.

SQLite enables foreign keys, WAL, transactions and a 20-second busy timeout.
Tables: users (case-insensitive unique email, salted scrypt hashes), symbols (ticker
PK and current source), prices (ticker/date PK, positive REAL close), news
(unique ticker/URL), watchlist (user/ticker PK and FKs), messages (owner-scoped),
rate_limits (bucket PK with serialized increments). Tests cover accounts, isolation,
CSRF, redirects, CSV, failures, chat contracts and unknown sentiment.

Local inventory (counts only, no personal records inspected): market-live.db had
0 users, 0 watchlist rows, 508 prices and 71 news; old market.db had 1 user,
6 watchlist rows, 1440 prices and 24 news. The old database is intentionally not
imported by the current application and must not be overwritten or removed.

## Weaknesses and security findings

- `f51fc78` tracks `env (1).txt` containing a DeepSeek credential, a session secret,
  both databases and bytecode. Historical documentation incorrectly claims these
  were ignored. Treat the credential and session secret as exposed; rotate/revoke
  them and invalidate old sessions. Treat tracked account/database records as an
  exposure requiring owner review. Removing files from HEAD does not erase history.
  No values are reproduced in this audit. No destructive history rewrite is planned.
- config.py implicitly reads both `.env` and `env (1).txt`. This must be removed;
  process environment becomes the only credential configuration source.
- Switching stock providers deletes prices. Current source provenance cannot describe
  older revisions. Preserve a source archive before refreshing the compatibility view.
- Float prices, ticker-only identity and date-only storage cannot represent streams.
- GET requests start daily background jobs. Preserve this compatibility for now;
  continuous ingestion belongs in a separate process, never a Flask handler.
- No migration/version/backup mechanism, feed health, queue limits or recovery ledger.
- No mail verification/recovery, market holiday/early-close calendar, streaming,
  forecasting, explainability, cloud service or provider redistribution entitlement.
- `data/market.db`, Checkpoint2.pdf and the PNG are legacy/reference material, not
  active data sources. Font OFL is a third-party license. Chart `is_market` marker
  support is unused but harmless. No speculative removal of existing UI/code.

## Changes selected for Phase A and first Phase B slice

Move Flask implementation into a package with backward-compatible `app.py` imports
and executable entry point. Add a separate v1 blueprint; preserve old contracts.
Add transactional additive SQL migrations with SQLite online backups; archive all
available stock observations by source before changing the legacy projection.
Add explicit instrument/provider-symbol registry, Decimal/UTC event contract,
source-specific event/state/checkpoint/quality storage and provider capability/license
metadata. Add Binance public streaming and closed daily-candle backfill in an asyncio
worker with bounded queues, heartbeats, rotation, retries and graceful shutdown.
Extend the current UI using its existing CSS classes and chart renderer.
Add MIT governance, local container preparation and CI checks.

## Breaking-change risks and recovery

Implicit credential files cease to work: export DEEPSEEK_API_KEY and SECRET_KEY.
Production must explicitly configure a strong session key and secure cookies behind
HTTPS. Development without a key uses an ephemeral key; sessions expire on restart.
Old exported imports/routes and database tables stay supported. `prices` remains a
single-source display projection; durable source archives and normalized events are
not deleted when providers change. Existing unavailable history cannot be recovered
from earlier destructive refreshes. Migration backups remain private and ignored.
A schema rollback restores the full backup while both processes are stopped; never
run old code against a partially downgraded schema.

## Deferred

Twelve Data, Alpaca IEX/SIP, FRED and additional markets are capability metadata only,
not operational feeds. Redis, browser WebSocket endpoint, account recovery,
one-year stock history, deterministic indicators, forecasting, XGBoost/SHAP,
production performance acceptance and cloud deployment require later phases.
No prices, predictions, license permissions or deployment success are invented.
