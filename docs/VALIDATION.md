# Earlier validation evidence

> Historical MVP evidence, not the complete current state. The later audit
> confirmed that credentials, a session secret and databases did enter Git in
> f51fc78; the earlier claim about .gitignore was incorrect. They were initially
> untracked without rewriting history. The branches were subsequently sanitized;
> exposed keys still require rotation. Current configuration uses only the process
> environment and loads no local files. See [SECURITY.md](../SECURITY.md),
> [the cleanup report](HISTORY_CLEANUP.md) and [the implementation report](IMPLEMENTATION_REPORT.md).

Date: 6 November 2026 (Asia/Shanghai).

## Result

The local implementation connects the application to a new SQLite database and
real external sources. Routes and integration tests pass. Live AI checks with a
valid credential and browser visual review were still pending at this stage.

## Verified

- Dependencies installed in the existing `venv/`: Flask 3.1.3 and Waitress 3.0.2.
- Python modules compiled and `static/app.js` syntax checked with Node.
- 19 integration tests passed, isolated in temporary databases.
- Actual startup with `./run.sh`, served by Waitress at `127.0.0.1:5050`.
- HTTP 200 for landing, overview, news, library, login, registration and AAPL
  details, plus CSS, JavaScript and the local font.
- `/health`: database connected and AI configuration detected. This endpoint
  does not certify DeepSeek connectivity.
- Real AAPL, MSFT, NVDA and SPY acquisition: **508 daily closes** and **71 RSS
  headlines**, persisted in `data/market-live.db`. These are capture counts,
  not permanent product figures.
- Price source for this capture: Nasdaq. Yahoo returned HTTP 403 from this
  environment; the fallback received and stored the series.
- IBM Plex Sans downloaded and served locally with its OFL license.
- The supplied key was absent from HTML, API responses and application source.
  The original assertion that credential files and `.env` were already excluded
  by `.gitignore` was incorrect; see the correction above.

## Coverage of the 19 tests

Rendering without data and without fictional seeding; registration, password
hashing and persistent watchlists; user isolation; login and local redirects;
CSRF and Origin; POST-only logout; private watchlists; unknown sentiment and
complete reaction windows; news filters; CSV and API provenance; server-derived
chat context and separate histories; explicit AI errors without a fabricated
saved response; invalid JSON; response-scope validation; validated, persisted
sentiment; rate limits; price preservation after provider failure; idempotency
and series replacement when changing provider; headers and absence of public secrets.

AI responses in these tests are mocked to verify contracts and logic. They are
not evidence of a real model's capabilities, accuracy or jailbreak resistance.

## Pending work and observed blockers at that stage

1. **DeepSeek:** a real chat request and model-endpoint check returned HTTP 401.
   The credential was loaded but rejected. The user deferred replacement. Live
   sentiment and chat were not validated in this review.
2. **Visual review:** browser connection returned `The browser access host is unavailable`
   and listed no browsers. No screenshots or visual acceptance of breakpoints,
   keyboard behavior, contrast, dark theme or phone behavior were obtained.
3. **Publication:** no external service was registered or deployed. The project
   uses Flask/Waitress; Sites hosting uses Workers and would require a runtime
   migration for an equivalent backend. Code and local startup were ready for review.

## Next acceptance checks identified then

- Replace the rejected key privately in the process environment, restart and test
  screen-related, conceptual, off-topic and investment-recommendation questions;
  verify cited sources and appropriate refusals. Current code does not load `.env`.
- Request real sentiment for an asset and check text, persistence and error states.
- Open landing, app and chat at 375, 768 and 1440 px; check navigation, local table
  scrolling, focus, zoom, keyboard and absence of overall page overflow.
- Follow registration → add asset → overview → details → source → CSV → chat → logout.
- Before commercial publication, review data licensing, HTTPS, secrets, account
  recovery, backups, monitoring and capacity.
