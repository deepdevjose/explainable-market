# Publish the full application independently of the laptop

Status: configuration prepared, **site not yet deployed**. A hosting account and
reachable machine are required. Tests and reading this document create no resources.

## What GitHub can host

GitHub stores source code and runs checks. GitHub Pages hosts HTML/CSS/JS; it
cannot run Flask, SQLite or the worker. The application is not replaced with a
screenshot, information page or account-free imitation of a deployment.

Full publication needs: GitHub → external Linux machine → public HTTPS.
A GitHub Pages page could optionally link to the final URL once it exists.

## Compatible free option: Oracle Cloud Always Free

1. The owner registers at https://signup.cloud.oracle.com. Oracle requests card-based
   identity verification and may place a temporary authorization hold. Do not share
   passwords, card details or private keys in chat or the repository.
2. In the home region, find an Ubuntu instance explicitly marked **Always Free**.
   Stay within quotas currently shown in the console, including boot volume,
   networking and additional services. Do not choose a paid machine or rely only
   on 30-day trial credits.
3. Stop if free capacity is unavailable. Do not upgrade to Pay As You Go to proceed.
   Free availability does not guarantee capacity or an SLA; Oracle may reclaim
   instances considered idle under its terms.
4. Create the VM with your own SSH key, public IP and persistent storage. Permit
   SSH only from the administrator's IP. HTTP 80 and HTTPS 443 must be reachable
   from the Internet for public access and TLS validation. Check both OCI network
   rules and Ubuntu's firewall. Do not expose 5050.
5. Install Docker Engine and Compose using the official Ubuntu instructions:
   https://docs.docker.com/engine/install/ubuntu/. Do not run third-party scripts.

Primary documentation consulted on 6 November 2026:

- https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
- https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- https://www.oracle.com/cloud/free/faq/

Render Free is not equivalent for this architecture: its filesystem is ephemeral,
it has no free persistent disk and can suspend after inactivity. SQLite accounts
must not depend on that filesystem: https://render.com/docs/free.

## Startup on the VM, not the laptop

These steps require a validated branch published on GitHub. Do not clone an old
version containing unsafe configuration. Once the validated version is published:

```bash
git clone --single-branch --branch main \
  https://github.com/deepdevjose/explainable-market.git
cd explainable-market
```

Choose a hostname pointing to the VM's IP. Without a domain, sslip.io or nip.io can
provide an IP-based name without purchasing a domain; they depend on external DNS.
Documentation example: `203.0.113.10.sslip.io` uses a reserved address and **must
not be used literally**. Replace it with the real public IP.

https://sslip.io/ documents resolution and TLS certificates for these names.

Create private configuration **once**, using the real hostname:

```bash
sudo python3 scripts/init_production.py --host YOUR_PUBLIC_HOST
sudo docker compose \
  --env-file /etc/market-explained/.env.production \
  -f infrastructure/deployment/compose.production.yaml config --quiet
sudo docker compose \
  --env-file /etc/market-explained/.env.production \
  -f infrastructure/deployment/compose.production.yaml up --build -d
```

The script generates SECRET_KEY on the server, mode 0600, outside the repository.
It does not print the value and refuses to overwrite existing configuration.
Docker explicitly receives the file and injects process variables; Flask does
not implicitly read credential files. DeepSeek is optional and must not use the
previously exposed credential.

Production Compose adds Caddy with automatic HTTPS, the web process, Binance
worker and daily collector. Only 80/443 are public. SQLite and certificates use
persistent volumes; processes restart after failure and the trusted proxy IP is
fixed. If subnet 172.30.0.0/24 conflicts with existing VM networking, change it
and keep the proxy IP and TRUSTED_PROXY aligned.

New volumes start without accounts. To transfer existing accounts, perform a
private SSH migration with a consistent backup as described in
[DATA_OPERATIONS.md](../../docs/DATA_OPERATIONS.md). Never upload the database to
the public repository. Do not mix WAL files between databases or use `down -v`.

## Verify publication

```bash
sudo docker compose \
  --env-file /etc/market-explained/.env.production \
  -f infrastructure/deployment/compose.production.yaml ps
sudo docker compose \
  --env-file /etc/market-explained/.env.production \
  -f infrastructure/deployment/compose.production.yaml logs --tail=50 proxy web worker
curl --fail https://YOUR_PUBLIC_HOST/health
```

Check from another connection: landing, registration/login, persistent watchlist,
markets, sources, CSV and Binance timestamps/status. Do not skip certificate
validation. Restart services and verify that a test account retains its watchlist.
Turn off the laptop and open the URL from another device to accept the independence
requirement. Only then record the URL as deployed.

Continuous trades grow SQLite. Monitor free disk, backups, RAM and freshness
before expanding pairs; this deployment does not automatically delete history to
fit a free quota. Always Free has operational limits.

## Update from GitHub

On the VM, fetch and review a validated branch commit before rebuilding:

```bash
git pull --ff-only
sudo docker compose \
  --env-file /etc/market-explained/.env.production \
  -f infrastructure/deployment/compose.production.yaml up --build -d
```

GitHub Actions SSH access and automatic private-key copying are not configured.
The laptop no longer runs the web app or worker once they run on the VM. Prepared
configuration does not mean a VM exists or a certificate was issued; both require
verification. This optional plan has not been deployed.
