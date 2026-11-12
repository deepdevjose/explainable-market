# Repository review before publication

This review prepares the working tree and index for a public commit. It neither
certifies absolute product security nor removes exposure from earlier commits.

## Scope of the 12 November 2026 review

- `.env.example` contains only empty credential fields and includes BigModel,
  DeepSeek and Twelve Data. Private service configuration remains unchanged.
- Databases, backups, keys, local configuration, logs, browser sessions and test
  screenshots are excluded from Git and the Docker context.
- The academic PDF with old credentials and an opaque reference image were
  untracked. They remained on disk; that initial step did not erase history.
- The README describes capabilities, limits, local setup and operating documents
  without depending on a temporary link or the author's private configuration.
- MIT, OFL, contributions, conduct, security policy and GitHub templates keep their
  responsibilities separate from financial data licensing.
- The publication check inspects the actual Git index as well as working files.
  Findings show paths and reasons, never credential values.

## Check commands

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/bandit -q -r market_explained ai.py charts.py collector.py config.py db.py -ll
.venv/bin/pip-audit -r requirements.txt -r requirements-ml.txt
node --check static/app.js
.venv/bin/python scripts/check_repository_hygiene.py
# After selecting only reviewed changes:
.venv/bin/python scripts/check_repository_hygiene.py --staged
git diff --cached --check
git status --short
```

Checks do not replace private review of the diff and any new binary files. Never
publish databases as fixtures or screenshots containing accounts, cookies or keys.
External tests and deployment require separate evidence.

### Results of this review

| Local check | Result |
| --- | --- |
| unittest, Python 3.12 | 79 tests passed; no external requests |
| Ruff / mypy | No issues; mypy checked 23 selected files |
| Bandit, application code and scripts | No medium/high-severity findings |
| pip-audit, runtime and ML dependencies | No known vulnerabilities in the audited resolution |
| JavaScript / Python compilation | Syntax and compilation passed |
| Local links in README, contribution, security and this document | Targets exist |
| Current private keys against reachable Git blobs | No matches in the targeted review |
| Known historical secrets against current publishable files | No matches |

Local results do not claim that remote GitHub Actions jobs or a Docker build
finished. Demo processes were not changed; the web service remained active.
Publication status is checked separately against the index.

## Pending outside the commit

The initial review found an old provider key, databases and session secret from
previous versions and a PDF with demo credentials. A historical configuration
example also contained a copy of the key. Cleanup of both published branches was
subsequently authorized and prepared, preserving the current tree and validating
it in an independent checkout. See [the cleanup report](HISTORY_CLEANUP.md).
Sensitive values are not published.

Current private service credentials and known historical secrets did not match
blobs in the sanitized history. Revocation of old keys, review of reused passwords
and possible GitHub cache removal remain pending. History replacement was an
exception explicitly authorized by the owner; private recovery is retained.

The public application remains a laptop-hosted demo. Neither this commit nor a
CI run is a permanent cloud deployment. Twelve Data display restrictions remain active.
