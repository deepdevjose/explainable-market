# Contributing

Use a feature branch and keep changes small. Preserve Flask, Jinja, SVG charts,
accessibility, local fonts, theme tokens and existing API contracts. Discuss
breaking changes and data-provider permissions before implementation.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt -r requirements-ml.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/bandit -q -r market_explained ai.py charts.py collector.py config.py db.py -ll
.venv/bin/pip-audit -r requirements.txt -r requirements-ml.txt
node --check static/app.js
.venv/bin/python scripts/check_repository_hygiene.py
# Review and select your files, then validate the exact staged content:
.venv/bin/python scripts/check_repository_hygiene.py --staged
git diff --cached --check
```

Tests use private temporary databases and fixed fixtures/local WebSockets, without
external API calls. Record provenance and UTC capture time for real fixtures;
never mark fixtures as live or seed them into the application. Add meaningful
migration-preservation and ingestion failure tests for relevant changes.

Never commit keys, local configuration, databases, backups or user records.
Keep all credential fields in `.env.example` empty; the application reads only
explicit process environment. Do not attach private logs or browser sessions to
issues. Existing historical exposures are documented in [SECURITY.md](SECURITY.md);
do not copy credentials out of old commits or rewrite shared history casually.
Use parameterized SQL and Decimal for new financial contracts. Keep provider
observations separate; never average feeds or infer instrument equivalence from
similar tickers. New migrations must be additive, transactional and backed up.
Document external tests separately from offline unit tests and visual acceptance.
Contributions are licensed under MIT for your original code. Data rights are separate.
