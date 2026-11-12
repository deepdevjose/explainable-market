# Public demo from a laptop

The laptop runs the existing Flask application, SQLite and real collectors.
Cloudflare Quick Tunnel provides a temporary HTTPS URL without the Microsoft
Dev Tunnels interstitial. This is not permanent hosting and does not guarantee
access from China. Keep the laptop awake and online during the demo.

## Supervised services

This Linux installation uses Python 3.12 in `.venv/` and the official Cloudflare
2026.10.7 binary, extracted without administrator privileges. Its SHA-256 was
checked against the official `pkg.cloudflare.com` package index. Opening the
website does not download or execute software on the visitor's device.

```bash
.venv/bin/python scripts/demo_services.py install
.venv/bin/python scripts/demo_services.py status
.venv/bin/python scripts/demo_services.py url
```

The installer creates six **user** services: `market-explained-demo-web`,
`-worker`, `-daily`, `-twelve`, `-forecast` and `-tunnel`. It enables
`loginctl enable-linger` so they start at boot and continue after logout. They
restart after failure and do not depend on an assistant process or open terminal.
The computer's suspend policy is unchanged. The server cannot work while the
laptop is asleep or off. Startup was configured, but the laptop was not physically
rebooted during validation. The daily collector polls every 900 seconds; Binance
receives WebSocket events and the interface reads persisted state every 5 seconds.

Private configuration lives in `~/.config/market-explained-demo/server.env`, mode
0600, with a stable session key generated once. It stays outside Git. Never reuse
historically exposed credentials. The server uses secure cookies and listens only
on loopback; the tunnel supplies HTTPS. Local HTTP is not a substitute for testing
registration/login through the public HTTPS URL. To select AI, set
`AI_PROVIDER=bigmodel`, `BIGMODEL_MODEL=glm-5.3-flash` and `BIGMODEL_API_KEY` in that
private file; the current installation already has a configured key. DeepSeek
remains available through `AI_PROVIDER=deepseek` and `DEEPSEEK_API_KEY`. Restart
only the web service. Never share keys.

```bash
systemctl --user restart market-explained-demo-web
journalctl --user -u market-explained-demo-worker -n 30 --no-pager
.venv/bin/python scripts/demo_services.py stop
.venv/bin/python scripts/demo_services.py start
```

Do not stop or restart the tunnel while recording: its URL changes when a new
Quick Tunnel connection is created. Run `url` again after restarting. Never share
databases, secrets or private configuration files.

## Languages and visible behavior

The selector supports Spanish, English and Simplified Mandarin Chinese (`zh-Hans`).
The choice persists in the session across pages. Catalogs are local: no external
translator receives headlines or personal data. Original news, company names,
saved chat text, attribution and quality codes remain in their original language.

Crypto prices are read every five seconds and flash green or red only when a
received observation changes. `prefers-reduced-motion` is respected. The short
crypto chart shows up to 60 observations **received during the visit**, rather
than every trade or an invented series; the historical SVG chart is preserved.
Stocks continue to use daily closes, never simulated real-time prices.

Without a key for the selected AI provider, the assistant supplies clearly
identified, local deterministic guidance for basic concepts. It neither classifies
headlines nor promises unrestricted conversation. Sentiment analysis still needs
a valid key and balance. Persistence, ridge and CPU XGBoost models train outside
the web server and appear at `/intelligence`. Twelve Data is polled every
15 minutes; observations are labeled DELAYED or STALE according to freshness.
Pending providers remain identified as pending. The landing-page illustration is
conceptual and labeled accordingly.

## Checks performed on 12 November 2026

This initial check preceded the market/forecast update below:

- 53 automated tests: the earlier 48 plus five for languages, isolation and local guidance.
- Twelve stocks updated through the 11 November close; news fetched.
- Recent real Binance events with LIVE status; storage preserved.
- Four user services active at that stage; `/health` and landing accessible over HTTPS.
- Chromium: language selector, Chinese/English, desktop/mobile and screenshot review.
- Local DNS initially failed to resolve the Quick Tunnel domain. HTTPS was checked
  using `curl --resolve` with an IP from a public resolver, retaining TLS validation.
  A later check also worked with normal DNS. This does not certify access from
  the teammate's device.

Before recording, open the URL on the recording computer, visit Markets and
check timestamps/status, registration, watchlist and CSV. A demo does not turn
public third-party endpoints into redistribution permission.

Static checks: Ruff passed, mypy found no issues in 14 selected modules, and
Bandit found no medium/high-severity issues in the reviewed scope.

## Update: markets and forecasts

Install `requirements-ml.txt` before running the service installer. The model
worker checks for new closes every 30 minutes and skips retraining when the
dataset hash has not changed. `-twelve` uses persistent local limits of 6 credits
per minute and 600 per 24-hour window, below the documented Basic allowance of
8/min and 800/day. Each request consumes a credit; other applications using the
same key can exhaust quota outside these counters.

Private configuration accepts `TWELVE_DATA_API_KEY` and
`TWELVE_DATA_PUBLIC_DISPLAY` (default 0). Keep the latter at 0 without external
display rights. Twelve Data prices and derivatives are hidden from all external
access, including history and assistant context. Direct internal loopback requests
allow inspection. After editing the private file, restart affected services:

```bash
systemctl --user restart market-explained-demo-web market-explained-demo-twelve
systemctl --user restart market-explained-demo-forecast
loginctl show-user "$USER" -p Linger
systemctl --user is-enabled market-explained-demo-web
```

The current installation verified `Linger=yes`, six active services and automatic
web recovery after terminating its process: a new PID and `/health` HTTP 200.
The tunnel was not restarted during that update, preserving its link. See the
[model report](PREDICTIVE_INTELLIGENCE.md) for results.

The assistant and headline classification now use **Zhipu / BigModel** in this
installation. The interface identifies the provider and model and explains the
submitted data. Numerical models and ingestion remain independent of AI. See
[AI provider validation](AI_PROVIDERS.md).

For step-by-step outage recovery and when the same link can be preserved, see
[TUNNEL_RECOVERY.md](TUNNEL_RECOVERY.md).

## Fedora 45: operation independent of VS Code

The six processes are systemd **user services**, enabled under `default.target`.
`loginctl enable-linger` keeps the user service manager running after logout and
starts it at boot. Closing VS Code or a terminal does not stop these services.
The installer uses `Restart=always` with a five-second delay, including recovery
from a clean process exit. An explicit `systemctl stop` still stops a service.

On 12 November 2026, all six services were verified active/enabled with
`Linger=yes`. The web process was deliberately terminated with SIGTERM; systemd
started a new PID automatically and local `/health` returned HTTP 200. Public
HTTPS `/health` and the landing page also returned HTTP 200 after recreating a
broken Quick Tunnel. No physical reboot or suspend/resume test was performed.

```bash
# Check service state, boot configuration and logout persistence.
.venv/bin/python scripts/demo_services.py status
systemctl --user is-enabled market-explained-demo-web market-explained-demo-tunnel
loginctl show-user "$USER" -p Linger
# Get the current temporary URL; older shared URLs can stop working.
.venv/bin/python scripts/demo_services.py url
# Inspect the tunnel connection without exposing private configuration.
journalctl --user -u market-explained-demo-tunnel -n 40 --no-pager
curl --fail http://127.0.0.1:5050/health
```

Cloudflare error 1033 means the requested hostname has no healthy tunnel
connection available to Cloudflare. It does not establish that Flask stopped or
that closing VS Code caused the outage. During this check, a tunnel reported a
registered connection but its public URL still returned 1033; recreating it
restored public access.

If local health works but the public tunnel remains broken, restart **only** the
tunnel, then read and verify its new URL before sharing it:

```bash
systemctl --user restart market-explained-demo-tunnel
.venv/bin/python scripts/demo_services.py url
# URL creation is asynchronous: repeat the previous command after startup.
```

A Quick Tunnel hostname changes when a new tunnel is created. A daemon does not
make that hostname permanent. Stable public naming requires a separately
configured named tunnel/hostname. The laptop must remain awake, powered and
connected; these services do not disable suspend or provide service while powered off.

References: [Cloudflare error 1033](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1033/)
and [Quick Tunnel limitations](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).
