# Implementation report — 6 November 2026

> Historical Phase A/B report. Later work and evidence are recorded in
> [PREDICTIVE_INTELLIGENCE.md](PREDICTIVE_INTELLIGENCE.md),
> [AI_PROVIDERS.md](AI_PROVIDERS.md) and [HISTORY_CLEANUP.md](HISTORY_CLEANUP.md).

## 1. Audit

The complete available history (a non-shallow repository with two original
commits), every Python module, template, CSS file, browser script, test and
operating document was inspected before code changes. All 19 original tests
passed as a baseline. [ARCHITECTURE_AUDIT.md](ARCHITECTURE_AUDIT.md) separates
verified capabilities, weaknesses, risks and deferred work.

Main findings: implicit credential loading, tracked secrets/databases/bytecode,
series deletion when changing provider, ticker-only identity, REAL prices and
no migrations, backups, streaming workers or CI.

## 2. Implemented architecture

An incremental modular monolith. `market_explained/application.py` contains the
existing Flask implementation; `app.py` preserves imports and executable/WSGI
entry points. New modules separate v1 APIs, contracts/instruments, providers,
worker and storage. Existing daily collection preserves compatibility and public
functions, now with independent Yahoo/Nasdaq adapters. Framework, frontend,
authentication and chart engine were not replaced.

## 3. New and modified files

- Added `market_explained/{api,markets,providers,ingestion,storage}/`, a SQL migration,
  `markets.html`, `market.html`, `sources.html`, documented fixtures and real
  REST/WebSocket captures, and configuration/migration/ingestion tests.
- Added `.env.example`, `.gitignore`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`,
  `CODE_OF_CONDUCT.md`, issue/PR templates, CI workflow, Ruff/mypy configuration,
  development dependencies, hygiene checker, Docker/Compose and architecture,
  data and deployment documentation.
- Modified `app.py`, `config.py`, `db.py`, `collector.py`, `ai.py`, `charts.py`,
  requirements/run.sh, README, navigation/base, overview, methodology, CSS and JS.
- Removed only from the Git index: credential file, local secret, both databases
  and bytecode. Local copies were retained. History was not rewritten in this phase.

## 4. Existing features preserved

Landing, overview, registration/login/logout, hashed accounts, private watchlists,
news/RSS/filters/sentiment, reaction windows, library, optional DeepSeek assistant,
isolated history, chat deletion and CSV. Earlier routes and formats, Jinja, SVG,
local IBM Plex, color/spacing tokens, light/dark themes, breakpoints and keyboard
controls remain. The 19 original tests were unchanged. Final visual review was
still pending: preserving CSS and HTTP rendering does not constitute visual acceptance.

## 5. New functionality

Explicit Binance Spot BTCUSDT and ETHUSDT registry, without confusing USDT and USD.
Canonical events validated with Decimal, UTC, provenance, sequence, prices,
bid/ask, volume, OHLCV and closed state. Immutable history, deduplication, ordering,
source/type-specific state, atomic checkpoints and quality records.

Independent asyncio worker: public trades/ticker/one-minute candle stream,
backfill of up to 365 closed daily candles, ping/pong, timeouts, rotation before
24 hours, jitter/backoff reconnects, resubscription, bounded queues, isolation
between REST/stream/provider tasks and shutdown with draining.

Integrated `/markets`, `/market/<symbol>` and `/sources` pages with filters/search,
provenance and dates. The interface polls the API every five seconds without
browser connections to the provider. Status derives from freshness and connection;
historical values are never promoted to LIVE. New paginated, rate-limited v1 APIs
have an error contract. A capability registry links each source's conditions.

## 6. Tests executed and results

- `venv/bin/python -m unittest discover -s tests -q`: **46/46 passed** on Python 3.14.
  Covers the original 19, migration/backup restoration, account/watchlist/message/
  news/price preservation, source provenance after provider changes, precision and
  validation, deduplication/order/checkpoints, historical/incomplete data, statuses,
  APIs, quotas, reconnect/resubscription on a local WebSocket, REST/provider failure
  isolation, queue draining and storage failure.
- Automated tests use no external API: fixed fixtures and dated, attributed real
  captures; the WebSocket server runs only on localhost. No fixture enters the
  active database or pretends to be a live feed.
- `venv/bin/ruff check .`: passed.
- `venv/bin/mypy`: passed for **14 selected files** in the new subsystem; this does
  not claim complete typing of the original Flask code.
- `venv/bin/bandit -q -r market_explained ai.py charts.py collector.py config.py db.py -ll`:
  no medium/high-severity findings. Fixed HTTPS calls have specific justified
  suppressions; external XML uses defusedxml.
- `venv/bin/pip-audit -r requirements.txt`: no known vulnerabilities at execution.
- `node --check static/app.js` and module `compileall`: passed.
- Git-index hygiene: no databases, local credentials, bytecode or key literals
  detected by the limited checker. This does not certify history.
- Actual startup **`PORT=5058 ./run.sh`**, Waitress with the active database:
  HTTP 200 for landing, app, news, learn, login, register, symbol/AAPL, markets,
  market/BTCUSDT, sources, health, CSV and checked APIs (16 HTTP checks).
- AAPL: 127 closes, Nasdaq source, latest close 2026-11-05 and no price_error when
  querying the runtime after refresh. Existing daily contracts remained intact.
- Browser: `The browser access host is unavailable`; no screenshots or visual
  verification of contrast, mobile behavior or real keyboard interaction.
- Docker was not installed: Compose/build/ARM64 were not run. The workflow was
  prepared without claiming that GitHub Actions ran.

## 7. Data migration

`001_market_foundation.sql` is additive and transactional, preceded by a mode-0600
SQLite online backup and a recorded version. Original tables remain. Old closes
are archived by provider, along with incoming revisions, before the compatibility
projection is updated. Provider changes do not delete the source archive. It
cannot recover data deleted by earlier versions or precision lost in REAL values.
Unknown stock-close timestamps are not invented.

Tests create an account, watchlist, conversation, news item and prices before
migration, initialize twice, compare rows and verify the restorable backup's
integrity. The old market.db remains intact and is not imported. See
[DATA_OPERATIONS.md](DATA_OPERATIONS.md) for procedure and limits.

## 8. Provider status and external evidence

**Binance implemented with a real connection verified.** Initial attempts against
stream.binance.com and data-stream.binance.vision timed out during handshake;
api.binance.com returned `Network is unreachable`. The official REST data endpoint
data-api.binance.vision responded. A later attempt connected successfully to
`wss://data-stream.binance.vision:443`.

A 25-second run persisted **1,734 stream events and 730 historical candles** for
the two pairs in a temporary database. A later 50-second active-database run
persisted **2,432 stream events** (2,294 trades, 92 ticker and 46 candle updates)
and **730 closed daily candles**. It shut down gracefully, with zero reconnects
in that run and SQLite integrity `ok`. Counts are point-in-time evidence, not
permanent figures or guaranteed throughput.

The API returned LIVE for both pairs during connection, with UTC timestamps and
provider=binance; after the worker stopped it returned STALE while preserving
the observation. Real frames of all three types and a REST response were captured
as fixtures. Historical values remain HISTORICAL. Complete local HTTP checks and
counts are in ignored artifacts/; databases are never published.

**Yahoo/Nasdaq:** daily acquisition preserved; Nasdaq verified in the runtime.
**Twelve Data/Alpaca/FRED at this stage:** capability/license metadata and planned
status, not operational adapters or credential requests. Forex, indices and
commodities showed absent data. SPY remained an ETF, not an index feed.

## 9. Known limits at this stage

No continuous 24-hour run: rotation was checked with local simulation. No complete
missed-trade/minute repair, durable queue after abrupt kill, automatic retention,
sustained-load benchmark or coordinated multiple workers. Checkpoints and gaps
persist; daily backfill is re-requested idempotently. Run one worker per database
and monitor growth.

No public `/api/v1/stream` WebSocket; the interface polls. At this stage the symbol
analysis and prediction APIs returned 501 rather than fabricated model data.
There were no Phase D ML/SHAP models or indicators. Auth/user/assistant separation
remained incremental, with functions in the preserved Flask module. DeepSeek
needed a new key and no live conversation was tested in this delivery. Visual,
container, cloud and ARM64 acceptance remained pending.

## 10. Security and licenses

Historical exposure of a DeepSeek credential, session secret and old account
records in databases was confirmed. **Revoke/rotate secrets and review exposed
data. Provider credentials were not rotated by this work.** Untracking files does
not erase history. No values were reproduced and no force push or rewrite occurred
in this phase. Earlier incorrect ignore documentation was corrected. Local-file
loading was removed; explicit environment configuration is required.

CSRF, password hashing, local redirects, CSP and secure cookies remain. Exact
proxy validation, required production keys, private SQLite permissions and secure
XML parsing were added. CI/hygiene checks are limited controls, not certification.
MIT covers original code; OFL and third-party data/news/material rights retain
their terms. No financial trades are executed.

## 11. Local commands

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
./run.sh
# Another terminal, same DATABASE_PATH or default directory:
venv/bin/python -m market_explained.ingestion.workers
```

Open http://127.0.0.1:5050/markets. No cloud account is required. For persistent
sessions, retain SECRET_KEY in a private manager/service instead of regenerating
it on each startup. `DEEPSEEK_API_KEY` is optional and exported only to the backend.

```bash
venv/bin/python -m pip install -r requirements-dev.txt
venv/bin/python -m unittest discover -s tests -v
venv/bin/ruff check .
venv/bin/mypy
node --check static/app.js
```

## 12. Next phase and change control identified then

Complete visual acceptance and extended streaming/rotation testing, measure
SQLite/disk behavior and add gap repair before expanding pairs. Then Phase C:
optional Twelve Data with quotas/licenses, Alpaca with separate IEX/SIP and FRED
macroeconomic integration. Follow with Phase D indicators and chronological
evaluation, starting with persistence without accuracy claims.

Changes were on `feat/multi-market-data-foundation`, with logical refactor,
ingestion/UI and operation/governance commits. At this historical delivery main
had not been merged, no push occurred and no cloud resources were created.
Docker, workflow and OCI instructions were preparation, not verified deployment.
