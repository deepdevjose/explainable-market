# Security policy

Report vulnerabilities privately using GitHub's **Report a vulnerability** feature
on this repository if enabled. If unavailable, open an issue requesting a private
reporting channel, without exploit details, credentials or personal records.
Do not post live keys, account data or database dumps in public issues.

## Known historical exposure

Early commits included a provider credential, a session secret, local databases
with legacy account records, and a PDF containing demo-account credentials. The
provider credential also appeared in an older configuration example. Treat all
previously exposed credentials as compromised, even if they no longer work.

On 12 November 2026, the repository history was sanitized with `git-filter-repo`:
credential files, databases, bytecode, the legacy PDF and screenshot were removed;
known exposed values were redacted from remaining historical text and commit
messages. Both `main` and `feat/multi-market-data-foundation` publish the current
application on the cleaned history. The current working tree was preserved;
local user data and the private service configuration were not published or reset.
A recovery copy of the old repository is stored privately outside this checkout.

The cleaned reachable history was checked for forbidden paths, selected token
patterns and known historical/current service secrets. No matches were found in
215 historical file versions before the final documentation update. All 79 tests
passed against a separate checkout of the cleaned history. These targeted checks
are not a guarantee that every possible secret has been identified.

Rewriting branches cannot revoke credentials or erase other people's clones,
forks, GitHub caches or inaccessible internal references. Revoke the exposed old
provider key and review any reused demo passwords; review old account records as
well. The current service uses separate private credentials and a stable private
session key, which were not found in the historical scan. Revocation of old keys
has not been performed by this repository change.

Collaborators must clone the cleaned repository again or carefully rebase reviewed
changes; do not merge or push the previous history. Previously shared commit IDs
have changed. See [the cleanup report](docs/HISTORY_CLEANUP.md) for scope and
GitHub's cache-removal procedure. A post-push check confirmed that GitHub still
served a known sensitive value from an old raw-file URL (HTTP 200). Branch cleanup
is complete, but removal from GitHub caches remains pending with GitHub Support.
Do not upload the private recovery copy.

## Checks before committing

```sh
python3 scripts/check_repository_hygiene.py
# Select only reviewed files with git add, then inspect the actual staged blobs:
python3 scripts/check_repository_hygiene.py --staged
git diff --cached --check
```

The checker rejects local databases, credential files, browser artifacts, nonempty
credentials in `.env.example`, private-key blocks and selected provider/token
patterns. It prints paths and reasons only. Its default scan includes nonignored
untracked files; `--staged` checks the exact index even if the working copy was
subsequently cleaned. It is a guardrail, not a full historical secret scanner.
Review diffs privately; do not paste them into public issues before checking.

## Operating assumptions

Use an explicit process environment, APP_ENV=production, a random SECRET_KEY of at
least 32 characters, HTTPS, and COOKIE_SECURE=1. No credential files are loaded.
Development without SECRET_KEY uses an ephemeral key. Credentials stay server-side.
Only configure TRUSTED_PROXY to an exact IP for your own proxy; never use `*`.
Waitress clears untrusted forwarded headers; only the configured proxy may supply
client IP/protocol. Configure the proxy to replace client-supplied forwarded headers.

CSRF, scrypt passwords, local redirects, CSP, HttpOnly/SameSite cookies and SQLite
rate limits remain enabled. Use one web service and one streaming worker per DB.
Restrict filesystem access to data and backups. Stop both services before restoring
a full backup. Keep offline copies and test restoration. Email verification,
password recovery, distributed rate limiting and independent penetration testing
are not implemented. This service never executes financial trades.
