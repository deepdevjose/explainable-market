# Local containers and optional OCI Always Free

No cloud account is needed. No resources are created by these instructions or CI.
Do not assume free capacity exists or approve a paid fallback. GitHub Pages cannot
run Flask, SQLite persistence, the asyncio worker or a WebSocket service.

## Local / ARM64

The Python slim base and requirements support amd64/arm64. CI prepares builds for
both architectures; inspect the actual CI result before claiming an ARM64 image works.

```sh
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
docker compose -f infrastructure/compose.yaml config --quiet
docker compose -f infrastructure/compose.yaml up --build -d
docker compose -f infrastructure/compose.yaml logs -f worker
curl http://127.0.0.1:5050/health
```

Compose uses a private named volume. It does not import host data automatically.
For existing accounts, stop both processes, use SQLite online backup to copy the
active database, then restore that copy into the volume as uid 10001 before startup.
Never use `down -v` on a volume containing accounts. See docs/DATA_OPERATIONS.md.
Do not expose the SQLite directory, container socket or database backups publicly.

## Optional OCI deployment plan (not executed)

1. In the OCI console, confirm an explicitly **Always Free eligible** compute shape,
   regional capacity, storage and network quotas. If unavailable, stop; do not create
   paid resources. Review current official terms at https://www.oracle.com/cloud/free/.
2. Use your own SSH key, minimal inbound firewall rules and a supported Linux image.
   Keep the service on loopback. Copy/clone the repository and select the validated
   feature/release commit. Install Docker using its official distribution instructions.
3. Provision a hostname and a trusted HTTPS reverse proxy on the host. Set
   APP_ENV=production, COOKIE_SECURE=1 and a stable generated SECRET_KEY using the
   service manager's private environment. Never commit it. Optionally configure a
   precise TRUSTED_PROXY IP only if the proxy forwards client IP/protocol.
4. Start Compose with the existing private volume. Confirm HTTPS certificate,
   secure cookies, CSRF, login, original pages, `/health`, worker freshness, SQLite
   writes and provider errors. Verify Binance availability from that region.
5. Configure encrypted off-host backups and restoration rehearsals, OS updates,
   disk/CPU monitoring, alerting for stale feeds and a maintenance restart policy.

Deployment, capacity, billing eligibility, runtime performance and physical ARM64
execution have not been verified here. CI builds are preparation, not deployment.
