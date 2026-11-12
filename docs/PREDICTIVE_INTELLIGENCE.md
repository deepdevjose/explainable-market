# Markets and forecasts — implementation and evidence

Update verified on 12 November 2026. The existing application was extended;
Flask, Jinja, SQLite, CSS, SVG and authentication were not replaced.

## Implemented

- Independent Twelve Data REST adapter: daily history and quotes with provider
  timestamps, Decimal prices and explicit provenance. It queries EUR/USD,
  USD/JPY, XAU/USD and two separately registered indices. Sources are not mixed
  and USDT is not identified as USD.
- Independent polling worker, persistent quotas of 6/min and 600/24 h,
  checkpoints, deduplication, conservative UTC closure, per-instrument status
  and recovery. Permanent rejections retry after 24 hours; network/quota failures
  after 60 seconds. Local accounting cannot track external use of the same key.
- Quotes polled every 900 seconds and labeled DELAYED, with contractual delay
  unverified. They become STALE when event or receipt age exceeds 1800 seconds.
  This adapter is not advertised as streaming or LIVE.
- Persistence, ridge autoregression and CPU XGBoost for the next observed close's
  return. Training is separate from Flask, requires at least 120 closes, checks
  every 30 minutes and uses a dataset hash to avoid duplicate training.
- SMA20, EMA20, RSI14 using simple averages, MACD without signal line,
  Bollinger20 bands, latest log return and 20-period daily log-return volatility.
  Volatility is not annualized with one calendar across all markets.
- `/intelligence`, `/api/v1/predictions/<symbol>` and `/api/v1/analysis/<symbol>`:
  model comparison, uncertainty, dates, quality, indicators and contribution
  explanations in es/en/zh-Hans.
- Six supervised, enabled systemd services with `Linger=yes`: web, Binance,
  daily collection, Twelve Data, models and tunnel. The app starts at laptop boot
  without VS Code remaining open. Suspension or shutdown interrupts service.

## Main files

| Area | Added or modified |
| --- | --- |
| Sources and polling | [Adapter](../market_explained/providers/twelve_data.py), [worker](../market_explained/ingestion/twelve_worker.py), capability registry and [persistence](../market_explained/storage/repository.py) |
| Models | [Forecasting](../market_explained/intelligence/forecasting.py), [series/registry](../market_explained/intelligence/data.py), [worker](../market_explained/intelligence/worker.py), [optional dependencies](../requirements-ml.txt) |
| API and access | [Routes](../market_explained/api/routes.py), [display authorization](../market_explained/security/display.py) |
| UI | [Forecast page](../templates/intelligence.html), existing navigation/details/explorer, language catalogs and existing CSS |
| SQLite | [Migration 002](../market_explained/storage/migrations/002_twelve_data.sql), [003](../market_explained/storage/migrations/003_verified_index.sql) |
| Operation and validation | [Services](../scripts/demo_services.py), [CI](../.github/workflows/ci.yml), [new tests](../tests/test_twelve_forecasting.py), [fixtures](../tests/fixtures/README.md), contract/migration test updates |

`tests/test_app.py` was not changed. The user's earlier `.env.example` edit was
left intact and outside the implementation commits described here.

## Methodology and limitations

Only complete closes from one specific source per instrument are used. Stocks
retain their current provider's historical attribution and a session date with a
conservative UTC cutoff, not the exact exchange close time. Candles retain their
window and receipt time. Provider revisions are stored as separate observations;
training uses the latest revision. This dataset is not a point-in-time archive
of information known on each date. Corporate adjustments, survivorship bias and
regime changes remain unresolved.

Each row's features use only prices known through its cutoff: two lagged returns,
5/20-session mean returns, volatility20 and distance from SMA20. The target is the
next observed close's simple return, not a guaranteed price or necessarily an
exact 24-hour horizon. Estimated price is derived from the reference price using
Decimal arithmetic; models use float arrays for numerical training.

Data is split chronologically into approximately 60% training, 20% calibration
and 20% testing. Calibration and testing use expanding-window retraining with
only targets available before each origin. Selection uses calibration MAE, never
the test segment. After evaluation, the selected model fits all known targets
and predicts from the latest close. Test results do not drive optimization.

The nominal 80% empirical interval uses a finite-sample quantile of absolute
calibration residuals from the selected model. **Future coverage is not guaranteed**:
series are dependent and change regimes. Actual test coverage is shown alongside
the nominal level. Models have no independent validation.

XGBoost uses 40 trees, depth 2, eta 0.05, regularization and a fixed seed, without
a GPU. Contributions use built-in TreeSHAP (`pred_contribs`); ridge reports
standardized feature contributions. They describe model calculations and do not
establish economic causes. Persistence estimates zero return. Library metadata
and the selected model's JSON artifact are stored in the private model registry;
the API does not expose the booster artifact.

No orders, brokers or promised returns. DeepSeek remains optional and does not
participate in ingestion, training, selection, intervals or numerical explanations.

## Real evidence from this installation

- Twelve Data: **1,095 closed candles and 3 quotes** across EUR/USD, USD/JPY and
  XAU/USD, normalized and persisted. Test fixtures were not seeded.
- SPX returned HTTP 404. The official `/indices` catalog confirmed FTSE with GBP
  currency and LSE venue; its request also returned HTTP 404. Both remain
  UNAVAILABLE without ETF substitution or synthetic prices. The HTTP code alone
  cannot establish whether the cause is plan, coverage or symbol.
- **17 persisted forecasts**: 12 stocks, 2 crypto pairs, 2 forex pairs and gold.
  Calibration selected persistence for 13 and XGBoost for 4. Ridge trained and
  was evaluated as a candidate but was not selected. Persistence is a legitimate,
  visible baseline.
- MSFT example: later test MAE was 0.01684 for persistence, 0.01852 for ridge and
  0.01795 for XGBoost; observed coverage of the selected interval was **50%** over
  22 observations. NVDA coverage was **36.36%** over 22 observations. This **does
  not establish predictive accuracy**: selected models can underperform the
  baseline outside calibration. The UI shows results without using that test
  to change the selected model or conceal low coverage.
- Existing rows before/after migration and model generation were preserved:
  1 account, 2 watchlist entries, 2 messages and 1,544 daily prices. Migration
  tests also covered accounts, watchlists, messages, news and prices in an older schema.
- Six services active and enabled; `Linger=yes`. Controlled web termination led
  systemd to create a new PID and `/health` returned HTTP 200. No physical reboot
  or continuous 24-hour acceptance test was performed.
- Public HTTPS: `/api/v1/predictions/MSFT` returned 200 with real XGBoost output;
  `/api/v1/market/EURUSD` returned UNAVAILABLE and `observation=null` due to external
  display restrictions. This provider's history/analysis/prediction endpoints
  return 403 for external visitors.

Counts are a validation snapshot, not continuous metrics. Binance continues to
receive events and the database can grow after this report.

## Validation executed

- Documented `./run.sh` launcher ran on a temporary port/database: `/health` HTTP 200.
- **63 unittest tests passed**, including the original 19 unchanged, migration/
  preservation, earlier contracts and ten new offline tests.
- New tests cover real Twelve Data fixtures, rejection of current open-day candles,
  timestamps/Decimal, deduplication, revisions, quotas, retries, absent credentials,
  safe errors, public display restrictions, causal features, walk-forward evaluation
  and forecast persistence/reading.
- CPU XGBoost installed and executed on this Linux amd64/Python 3.12 laptop. ML
  tests explicitly skip when dependencies are absent; a separate CI job installs
  them. Remote CI and ARM64 ML execution have not been verified.
- Ruff and mypy (22 selected files) passed. Bandit had no medium/high findings;
  runtime/ML `pip-audit` found no known vulnerabilities.
- Chromium over HTTPS: desktop prediction page in Spanish/English and Chinese
  mobile at 390 px, scrollable tables, presentation-rounded prices, no overall
  horizontal page overflow and no console messages.

Real fixtures are retained only for offline tests. Model-test series are generated
in memory to verify causal features and persistence; they are not loaded into
workers or the production database.

## Migrations and security

`002_twelve_data.sql` adds instruments/provider_symbols, per-instrument retry
status and a prediction index. `003_verified_index.sql` adds FTSE from the official
catalog. SPX and all history remain. Each run with pending migrations creates a
private mode-0600 SQLite backup before the transaction. See
[DATA_OPERATIONS.md](DATA_OPERATIONS.md) for restoration and storage.

No credentials were committed by this implementation. The new key exists only
in the private mode-0600 service environment; errors/logs use controlled codes.
Because the key was shared in conversation, rotation and private replacement are
recommended. Earlier exposure remains documented in [SECURITY.md](../SECURITY.md).

`TWELVE_DATA_PUBLIC_DISPLAY` defaults to `0`. A key does not prove redistribution
rights: public Twelve Data prices, history and derivatives remain blocked until
authorization is confirmed. Direct internal loopback access without proxy headers
allows inspection. The data is excluded from public assistant context. Other
providers retain their own conditions.

## Running and next steps

The [README](../README.md) gives local commands and [LAPTOP_DEMO.md](LAPTOP_DEMO.md)
describes services/private configuration. The complete server retains SQLite
and workers; Cloudflare Workers would require persistence and execution migration.
Cloudflare Tunnel publishes the laptop server rather than hosting it in the cloud.
Quick Tunnel links can change.

Next: confirm display rights and index coverage/plan, validate quotas for 24 hours,
establish a stable URL if a domain is available, improve point-in-time archives,
calendars/adjustments and evaluate more out-of-sample data. ATR, MACD signal,
volume/cross-market correlations, neural models, Alpaca/FRED, browser WebSockets
and permanent external deployment remain pending. No predictive edge has been
established; additional model complexity should depend on validation.

## Primary references

- [Official Twelve Data SDK](https://github.com/twelvedata/twelvedata-python).
  The adapter implements the REST contract directly without requiring the SDK.
- [Time series](https://twelvedata.com/docs/market-data/time-series),
  [quotas](https://support.twelvedata.com/en/articles/5615854-credits),
  [plans](https://twelvedata.com/pricing),
  [usage and redistribution](https://support.twelvedata.com/en/articles/5332349-commercial-and-personal-usage),
  [attribution](https://support.twelvedata.com/en/articles/12647398-attribution-guidelines-for-using-twelve-data).
- [Python on Cloudflare Workers](https://developers.cloudflare.com/workers/languages/python/).
- [CPU XGBoost](https://xgboost.readthedocs.io/en/stable/install.html).
