# Security policy

Report vulnerabilities privately using GitHub's **Report a vulnerability** feature
on this repository if enabled. If unavailable, open an issue requesting a private
reporting channel, without exploit details, credentials or personal records.
Do not post live keys, account data or database dumps in public issues.

## Known historical exposure

Commit `f51fc78` included `env (1).txt` with a DeepSeek credential,
`data/.session-secret`, and both local databases (including legacy account records).
These paths are removed from tracking and ignored in the foundation branch; local
copies are retained. The original history remains reachable. Treat all credentials
in that history as compromised even if a provider previously rejected them.

The owner must revoke/rotate the exposed provider credential, export a new
SECRET_KEY, restart the web process to invalidate old sessions, and review exposed
account records and any reused passwords. Credential revocation was not performed
by this change. Do not reactivate or redistribute the historical credential file.
A separate, coordinated history cleanup may reduce accidental exposure but does
not replace rotation and is outside this non-destructive change.

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
