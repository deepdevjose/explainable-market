<div align="center">
  <img src="static/mark.svg" width="56" height="56" alt="Explainable Market">
  <h1>Explainable Market</h1>
  <p>Sourced market data. Understandable context. Forecasts with uncertainty.</p>
  <p><strong>English · Spanish · Simplified Chinese</strong></p>
  <p><a href="#local-setup">Quick start</a> · <a href="#features-and-status">Features</a> · <a href="docs/ARCHITECTURE_AUDIT.md">Architecture</a> · <a href="docs/demo-day/README.md">Presentations</a> · <a href="CONTRIBUTING.md">Contributing</a> · <a href="SECURITY.md">Security</a></p>
</div>

An open-source platform for exploring prices, news and financial concepts.
It preserves Flask, Jinja, native JavaScript and server-generated SVG charts,
with optional AI services and a frontend that does not depend on a CDN.

**Information and education only.** The platform does not connect brokerage
accounts, execute orders or promise returns. Estimates can fail; a coincidence
in timing or a model contribution does not establish causation.

## Features and status

| Area | Implemented | Current limits |
| --- | --- | --- |
| US stocks | Yahoo/Nasdaq daily closes, RSS news and CSV export | Historical prices, not live quotes; 12 initial instruments |
| Cryptocurrencies | Public Binance trades, ticker, candles and backfill | BTCUSDT and ETHUSDT; quoted in USDT, not USD |
| Forex and gold | Optional Twelve Data REST: EUR/USD, USD/JPY and XAU/USD | Quotas and licensing; external display disabled by default |
| Forecasting | Persistence, ridge and optional CPU XGBoost; chronological evaluation | At least 120 closes; no independent validation or guaranteed accuracy |
| Assistant and sentiment | Optional BigModel or DeepSeek, bounded context and validated JSON | Valid credentials required; local educational guidance when no key is configured |
| User experience | Registration, sessions, persistent watchlists, library and three languages | No password recovery or email verification |

SPX/FTSE indices remain unavailable with the access tested. Alpaca, FRED, forex
streaming and browser WebSocket delivery are pending. The web interface polls
persisted state every five seconds; Binance streaming runs in a separate worker.
No synthetic prices are generated to fill markets without data.

### Reading the charts

- **Green / red / gray:** each observed price rises, falls or stays unchanged relative to the previous observation.
- **Dashed yellow:** the estimated next close, whether it rises or falls.
- **Yellow shading:** a nominal 80% empirical interval; future coverage is not guaranteed.

`/intelligence?symbol=BTCUSDT` shows up to 30 closes through the model's data
cutoff and its forecast. Source, cutoff and reference price are checked before
joining them. The future horizon's width is illustrative and does not invent a
trading session. Source attribution, UTC dates and limitations remain visible.

## Local setup

Requires Python 3.11 or newer. Current local validation uses Python 3.12.

```bash
git clone https://github.com/deepdevjose/explainable-market.git
cd explainable-market
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
./run.sh
```

Open **http://127.0.0.1:5050**. Waitress serves the application without a debugger.
The launcher supports `.venv/` and the legacy `venv/` environment. A fresh
installation starts without credentials; external markets may be slow or unavailable.

Set a private, stable `SECRET_KEY` to retain sessions across restarts. Development
uses an ephemeral key when none is configured. Production requires a stable key.

### Private configuration

[.env.example](.env.example) documents variables **without credentials**. The
application reads the process environment; it does not automatically load `.env`
or legacy files. Use a secret manager or private service configuration. Never put
real values in examples, commits, issues, screenshots or shared commands.

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Stable session secret; at least 32 characters in production |
| `APP_ENV`, `COOKIE_SECURE`, `TRUSTED_PROXY` | Production mode, HTTPS and an exact trusted proxy |
| `DATABASE_PATH` | SQLite path; defaults to `data/market-live.db` |
| `AI_PROVIDER` | `deepseek` (compatibility default) or `bigmodel` |
| `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL` | Optional DeepSeek assistant |
| `BIGMODEL_API_KEY`, `BIGMODEL_MODEL` | BigModel assistant; default model `glm-5.3-flash` |
| `TWELVE_DATA_API_KEY` | Optional market provider, independent of AI |
| `TWELVE_DATA_PUBLIC_DISPLAY` | Defaults to `0`; change only after confirming external display rights |

Keys stay on the server. Users can see which AI provider receives their question
and context. Without a selected key, the app provides clearly identified local,
non-generative guidance. A configured provider's failure produces an error rather
than silently switching providers. See [AI configuration and validation](docs/AI_PROVIDERS.md).

### Collectors and models

Run each process in a separate terminal with the same `DATABASE_PATH`:

```bash
# Stocks and news; omit --loop for a single run.
.venv/bin/python collector.py --loop --interval 900
# Crypto streaming and closed-candle backfill.
.venv/bin/python -m market_explained.ingestion.workers
# Optional: Twelve Data polling with persistent quota accounting.
.venv/bin/python -m market_explained.ingestion.twelve_worker
# Optional: training outside the web server.
.venv/bin/python -m pip install -r requirements-ml.txt
.venv/bin/python -m market_explained.intelligence.worker
```

The last two workers support `--once`. Binance ingestion does not need a key.
Models use chronological splits and walk-forward evaluation; they do not train
on open candles or mix feeds. See [methods, results and limits](docs/PREDICTIVE_INTELLIGENCE.md).

## Data, persistence and API

SQLite uses WAL, foreign keys and transactions. Migrations are additive,
versioned and preceded by a private backup. They preserve accounts, watchlists,
messages and source-specific history. See [backup and recovery](docs/DATA_OPERATIONS.md).

Normalized market events retain provenance, decimal prices and UTC timestamps.
Statuses distinguish **LIVE, DELAYED, HISTORICAL, STALE, DEMO and UNAVAILABLE**.
LIVE requires recent events and receipts and a connected collector. Stopping
the worker preserves the last observation and makes it stale; it does not turn
that observation into new data.

| Page | Content |
| --- | --- |
| `/app`, `/watchlist`, `/symbol/AAPL` | Overview, personal watchlist and stock details |
| `/markets`, `/market/BTCUSDT` | Explorer and instruments with provider attribution and freshness |
| `/intelligence` | Forecast, chart, evaluation and contributions |
| `/news`, `/learn`, `/sources` | News, education and source status |

Existing routes remain supported. The v1 read API includes `/markets`,
`/instruments`, `/market/<symbol>`, `/market/<symbol>/history`, `/analysis/<symbol>`,
`/predictions/<symbol>`, `/providers/status` and `/system/health` under `/api/v1`.
Lists paginate with `limit` (1–200) and `offset`. Errors use
`{"error":{"code":"…","message":"…"}}`; persistent per-IP limits apply.
Forecasts return 503 when data or training is missing and 403 when display is
restricted. `/health` checks the database; `ai_configured` indicates configuration
only, not account balance or external availability.

### The data translation layer

Source-specific adapters receive JSON through APIs and WebSockets, and news
through RSS/XML. They map supported inputs to consistent records with validation,
source attribution and timestamps. News and market events use separate contracts.
The sentiment workflow sends headline IDs and text as JSON to the configured AI
provider and filters invalid response entries before storage. This makes the
integration more predictable; it does not establish an improvement in model accuracy.
CSV price export and JSON read APIs are implemented. Generic CSV/Excel imports
and dedicated BI connectors are extension opportunities, not active integrations.

## Development and checks

```bash
.venv/bin/python -m pip install -r requirements-dev.txt -r requirements-ml.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/bandit -q -r market_explained ai.py charts.py collector.py config.py db.py -ll
.venv/bin/pip-audit -r requirements.txt -r requirements-ml.txt
node --check static/app.js
.venv/bin/python scripts/check_repository_hygiene.py
# After selecting files with git add, inspect the exact proposed commit:
.venv/bin/python scripts/check_repository_hygiene.py --staged
```

Tests use temporary databases, fixtures and local WebSockets without external
requests. GitHub Actions configures tests, lint, type checks, dependency auditing
and amd64/ARM64 builds. External and visual evidence is documented separately;
a CI or deployment configuration does not prove that it has run successfully.

## Architecture and operation

```text
app.py                  Compatible Flask/WSGI entry point
market_explained/       API, markets, providers, ingestion, intelligence and storage
collector.py / ai.py    Compatible historical acquisition and educational integration
config.py / db.py       Explicit configuration and SQLite operations
charts.py               SVG charts without a CDN
templates/ / static/    Jinja, existing design, JavaScript and local fonts
tests/                  Isolated tests and fixtures with provenance
docs/                   Audit, protocols, validation evidence and presentations
infrastructure/         Docker Compose and deployment preparation
```

- [Architecture audit](docs/ARCHITECTURE_AUDIT.md) and [initial implementation report](docs/IMPLEMENTATION_REPORT.md).
- [Tunnel recovery and link preservation](docs/TUNNEL_RECOVERY.md): diagnose outages, preserve a running tunnel when possible and understand when a new URL is required.
- [Supervised Linux laptop demo](docs/LAPTOP_DEMO.md): startup services and temporary tunnel. Requires an awake, connected computer; it is not independent hosting.
- [Deployment and Docker](infrastructure/deployment/README.md): optional preparation, not a certified cloud deployment. GitHub Pages cannot run Flask or its workers.
- [Release review](docs/RELEASE_CHECKLIST.md): check scope and historical exposure.
- [Demo Day presentations and speeches](docs/demo-day/README.md): separate commercial and technical English pitches, with speaker notes.

## Security and licenses

**Sensitive material was exposed historically.** The published branches were
sanitized while preserving the current application. This does not revoke keys
or remove earlier copies, forks or GitHub caches. Read [SECURITY.md](SECURITY.md)
and [the cleanup report](docs/HISTORY_CLEANUP.md) before reusing credentials
or changes from old clones.

Original code uses [MIT](LICENSE); IBM Plex retains its [OFL](static/fonts/OFL.txt).
External news and data retain their original rights: free or public access does
not grant redistribution permission. `/sources` identifies provider conditions.
Twelve Data is hidden externally by default.

Read the [contribution guide](CONTRIBUTING.md), [code of conduct](CODE_OF_CONDUCT.md)
and [security policy](SECURITY.md). We preserve the existing design and
educational features through incremental changes.
