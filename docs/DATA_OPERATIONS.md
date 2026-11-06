# Data contracts, migration and recovery

## Storage

`db.py` is retained for legacy imports and parameterized SQLite access. The package
storage repository owns new events, projections and checkpoints. Schema version
`001_market_foundation.sql` adds tables and indexes without renaming or dropping
users, symbols, prices, news, watchlist, messages or rate_limits.

Before the first upgrade, SQLite's online backup API copies the whole database,
including committed WAL contents, into a private 0600 file under sibling `backups/`.
Failure to back up aborts migration. SQL statements, registry seed, archival copy
and version marker are applied in one `BEGIN IMMEDIATE` transaction. Concurrent
processes re-check version markers after locking. New DBs also get a baseline
backup. Runtime database files are restricted to 0600. Never commit any of them.

`stock_observations` preserves all available daily closes with provider, session
date, Decimal-compatible text values and original receipt time. Each refresh archives
both the old projection and incoming data before updating `prices`. Changing provider
may rebuild the compatibility `prices` view/table to avoid mixing adjustments; the
source archive is never deleted. Existing REAL prices cannot regain precision or
provenance that was already lost. Unknown old source is `legacy:unknown`.
Stock session dates are not invented UTC closing instants: v1 snapshot returns
`event_time: null` and `session_date` with a timestamp-quality flag.

New tables: instruments, provider_symbols, market_events, market_state,
ingestion_checkpoints, provider_health, data_quality, model_metadata and
prediction_history. The last two reserve storage contracts only; no models exist.
Provider-specific events are immutable and uniquely identified; current state is a
source-specific monotonic projection by instrument/event stream, never an average.
No cross-provider price consolidation policy is implemented.

## Canonical event

`MarketEvent` is a frozen, validated dataclass. Required fields preserve event ID,
instrument ID, provider, provider symbol, asset class, event type, UTC event and
receipt times, Decimal price/bid/ask/volume, quote currency, provider sequence,
quality flags and acquisition status. JSON/SQLite financial values are decimal
strings. Nullable fields remain null; quotes require valid two-sided prices.
OHLCV adds interval, open/high/low, candle-open time and closed state. Incomplete
streaming candles are retained as incomplete and never used as closed history.

Identities include venue and quote currency: `binance:spot:BTCUSDT` is BTC/Tether
on Binance Spot. `BTC-USD` and `BTC/USD` are not aliases. An unregistered provider
symbol is rejected. SPY remains a stock/ETF record, not comprehensive index coverage.

Duplicates are ignored without advancing checkpoints. Out-of-order observations
are stored with a quality flag but cannot rewind state/checkpoints. Trade sequence
resolves equal-millisecond order. Checkpoints commit atomically with the event.
LIVE is the original transport classification, not a timeless freshness promise.
The snapshot API computes current status: a live observation becomes STALE after
30 seconds of event/receipt age or if its worker is disconnected. Daily backfill
stays HISTORICAL. Empty storage is UNAVAILABLE. DELAYED and DEMO are supported
contracts but no delayed/simulated adapter is enabled.

## Worker and recovery

```sh
venv/bin/python -m market_explained.ingestion.workers
venv/bin/python -m market_explained.ingestion.workers --duration 60 --backfill-days 7
```

One stream for BTCUSDT/ETHUSDT subscribes to trades, ticker and UTC one-minute
klines. A 1000-event bounded queue applies backpressure; one writer serializes
SQLite transactions. REST backfill independently requests up to 365 closed daily
candles per instrument. Socket buffers are bounded too. Server ping/pong is handled
by websockets, with client ping/timeouts and planned rotation at 23h50m. New
connections re-subscribe using the same explicit combined-stream URL. Reconnects
use exponential backoff with jitter capped at 60 seconds; each gap is recorded.
REST retries five times and never prevents streaming. SIGINT/SIGTERM cancel
producers and allow 30 seconds to drain the queue. Storage failures terminate the
worker rather than claiming a write succeeded. Restart with a service manager.

Durable checkpoints establish the last persisted event. Restart/reconnect re-fetches
daily candles idempotently, but **does not replay all missed trades or minute candles**.
Gaps are explicit; full sequence-based gap repair is deferred. In-memory pending
events cannot survive a hard kill. Run one worker per database; throughput/storage
retention, batching and disk capacity require measurement before expanding pairs.
No retention job silently deletes history. No Redis backend is needed for this slice.

## Private backup and restore

Stop worker and web for a restore. For a consistent online manual backup:

```sh
venv/bin/python - <<'PY'
import db
from market_explained.storage.database import backup
with db.connect() as connection:
    print(backup(connection, db.DB_PATH))
PY
```

Record the code commit and schema versions with your private backup. Rehearse
restoration on a separate path; check `PRAGMA integrity_check`, user/watchlist counts
and login before replacing an active DB. For a rollback, stop both services, move
the current DB plus its `-wal`/`-shm` files to a private quarantine directory, copy
the full pre-migration backup to the configured database path, restrict permissions,
and start the matching old commit. Never restore by mixing WAL files from different
snapshots. `data/market.db` is historical/reference data and remains untouched.
