# Recover access to the laptop demo

## Can I recover the same link?

**Sometimes, while the same Quick Tunnel process is still running.** Restarting
only Flask or a market worker leaves the tunnel process untouched, so its URL
can normally stay the same. A temporary network interruption may also recover
without replacing the tunnel, but this is not guaranteed.

**If the Quick Tunnel process stopped or was recreated, its old random hostname
cannot be reclaimed through this setup.** A new process creates a new temporary
`trycloudflare.com` URL. This includes a laptop reboot or an automatic restart of
the tunnel process. Saving the old URL does not reserve it. Cloudflare documents
that [the hostname changes each time a Quick Tunnel is created](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

| Situation | Same link? | First action |
| --- | --- | --- |
| VS Code or a terminal was closed | Normally yes: systemd owns the services | Check local health and service state |
| Flask stopped but the tunnel is still running | Normally yes | Start/restart only `-web` |
| Prices stopped updating but the page opens | Normally yes | Inspect only the affected collector |
| Wi-Fi briefly disconnected or laptop resumed | Possibly, if the original tunnel survived | Restore connectivity and allow reconnection |
| Tunnel process restarted, or laptop rebooted | No reliable recovery of the old random URL | Retrieve and verify the newly generated URL |
| A permanent public address is required | Quick Tunnels cannot provide this | Configure a named tunnel with a stable hostname |

## 1. Open a terminal in the project

On this Fedora installation:

```bash
cd "$HOME/Documents/GitHub Repositories/new/explainable-market"
```

Keep the laptop awake and connected. Closing VS Code is safe; suspension or
shutdown interrupts access. Do not run the install/stop/start commands for all
services as the first recovery step: they may recreate the tunnel unnecessarily.

## 2. Check the application before touching the tunnel

```bash
curl --max-time 10 --fail http://127.0.0.1:5050/health
systemctl --user is-active market-explained-demo-web market-explained-demo-tunnel
```

A healthy local response includes `"status":"ok"`. `active` only means a process
is running; it does not prove that its public connection is healthy.

If local health fails, inspect and restart **only the web service**:

```bash
journalctl --user -u market-explained-demo-web -n 40 --no-pager
systemctl --user restart market-explained-demo-web
curl --max-time 10 --fail http://127.0.0.1:5050/health
```

Startup is asynchronous; repeat the health check after a few seconds if needed.
This does not restart the tunnel. Once local health succeeds, try the existing
public link again, including its `/health` path.

## 3. Local health works, but the public link fails

Check Internet connectivity and the tunnel without stopping it:

```bash
systemctl --user status market-explained-demo-tunnel --no-pager
journalctl --user -u market-explained-demo-tunnel -n 40 --no-pager
.venv/bin/python scripts/demo_services.py url
```

Compare the reported URL with the one being opened. After a restart, an old
bookmark or QR can still point to the previous tunnel. The helper reads recent
logs: its output alone does not prove that the URL is current or reachable.

If the original tunnel is reconnecting after a network interruption, restore
network access and allow it time to reconnect before restarting it. If public
access returns, the same link has been preserved. Do not repeatedly restart it.

Error 1033 concerns Cloudflare's tunnel connection, not necessarily Flask. A
running process, or even a logged registered connection, does not guarantee the
public route works. See [Cloudflare's error 1033 guide](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1033/).

## 4. Last resort: recreate the tunnel and obtain a new link

**This can change the URL. It does not recover the old random hostname.**
Use this when the tunnel has stopped or remains unusable after network recovery:

```bash
systemctl --user restart market-explained-demo-tunnel
```

Wait for startup, then retrieve the URL from the **current service invocation**:

```bash
tunnel_invocation=$(systemctl --user show market-explained-demo-tunnel --property=InvocationID --value)
journalctl --user -u market-explained-demo-tunnel \
  "_SYSTEMD_INVOCATION_ID=$tunnel_invocation" --no-pager -o cat \
  | rg -o 'https://[a-z0-9-]+\.trycloudflare\.com' | tail -n 1
```

If no URL appears, startup may still be in progress or may have failed. Repeat
the log check and inspect service status. Do not use a URL from an older invocation.
For a long-running tunnel, the original URL log may have rotated out of the journal;
keep a private note of the verified link without restarting a healthy tunnel.

Replace the example hostname below with the newly reported URL and check it:

```bash
curl --max-time 20 --fail https://YOUR-NEW-HOST.trycloudflare.com/health
```

Confirm HTTP 200, the landing page and a market page from the recording device
or another connection. Update shared links and QR codes only after that check.
Never disable TLS verification with `-k` to make a failed check appear successful.

## 5. If the page works but prices are stale

Do not restart the tunnel. Inspect the relevant worker first:

```bash
systemctl --user status market-explained-demo-worker --no-pager
journalctl --user -u market-explained-demo-worker -n 40 --no-pager
```

If that worker has failed, restart only it:

```bash
systemctl --user restart market-explained-demo-worker
```

Service suffixes are `-worker` for Binance, `-daily` for stocks/news, `-twelve`
for Twelve Data and `-forecast` for model training. Provider outages, quotas or
display restrictions can prevent fresh data even with a healthy worker; a restart
does not bypass them. Stock closes remain historical and model updates are not ticks.

## 6. Keep services independent of VS Code

```bash
systemctl --user is-enabled market-explained-demo-web market-explained-demo-tunnel
loginctl show-user "$USER" -p Linger
```

Expected: both services are `enabled` and `Linger=yes`. If disabled:

```bash
systemctl --user enable market-explained-demo-web market-explained-demo-worker \
  market-explained-demo-daily market-explained-demo-twelve \
  market-explained-demo-forecast market-explained-demo-tunnel
loginctl enable-linger "$USER"
```

Enabling does not restart an already running tunnel. If a service is inactive,
start only that service. Starting an inactive tunnel produces a new temporary URL.
A permissions error from `loginctl` requires local administrator assistance; do
not paste passwords or private configuration into chat or public issues.

## A permanent link needs different configuration

Use a Cloudflare account and a named tunnel published on a stable hostname under
a domain you control. Keep that tunnel identity and DNS configuration, and run
its connector as a supervised service. Then the public hostname can remain the
same across connector restarts, although access still requires the laptop and
network to be available. This has **not** been configured by this guide and does
not reclaim an old random `trycloudflare.com` hostname. See
[Cloudflare Tunnel setup](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/).

For the current temporary setup, retrieve the new URL after tunnel recreation.
Never delete SQLite data, regenerate the session secret or reinstall the whole
application merely to repair a public link. Keep logs private and review them
before sharing; never share `server.env`, keys, databases or backups.

See also [laptop operation](LAPTOP_DEMO.md), [backup and recovery](DATA_OPERATIONS.md)
and [security policy](../SECURITY.md).
