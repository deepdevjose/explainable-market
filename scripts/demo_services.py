#!/usr/bin/env python3
"""Supervise a laptop demo with user services, without passwords or root access."""
import argparse
import os
from pathlib import Path
import re
import secrets
import subprocess

ROOT = Path(__file__).resolve().parent.parent
PREFIX = 'market-explained-demo'
SERVICES = ('web', 'worker', 'daily', 'tunnel')


def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)


def quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%') + '"'


def install():
    python = ROOT / '.venv/bin/python'
    tunnel = ROOT / 'artifacts/tools/cloudflared-package/usr/bin/cloudflared'
    if not python.exists() or not tunnel.exists():
        raise SystemExit('Prepare .venv and the official cloudflared binary first.')
    config_dir = Path.home() / '.config' / PREFIX
    config_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    env = config_dir / 'server.env'
    if not env.exists():
        fd = os.open(env, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            stream.write('APP_ENV=production\nCOOKIE_SECURE=1\nHOST=127.0.0.1\nPORT=5050\n'
                         'TRUSTED_PROXY=127.0.0.1\nSECRET_KEY=' + secrets.token_hex(32) + '\n')
    units = Path.home() / '.config/systemd/user'
    units.mkdir(parents=True, exist_ok=True)
    commands = {
        'web': [python, ROOT / 'app.py'],
        'worker': [python, '-m', 'market_explained.ingestion.workers'],
        'daily': [python, ROOT / 'collector.py', '--loop', '--interval', '900'],
        'tunnel': [tunnel, 'tunnel', '--url', 'http://127.0.0.1:5050',
                   '--protocol', 'http2', '--no-autoupdate'],
    }
    for name, command in commands.items():
        unit = f'''[Unit]
Description=Market Explained demo {name}
After=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
WorkingDirectory={str(ROOT).replace(chr(37), chr(37)*2)}
EnvironmentFile={str(env).replace(chr(37), chr(37)*2)}
Environment=PYTHONUNBUFFERED=1
ExecStart={' '.join(quote(arg) for arg in command)}
Restart=on-failure
RestartSec=5
TimeoutStopSec=45
UMask=0077
NoNewPrivileges=true

[Install]
WantedBy=default.target
'''
        (units / f'{PREFIX}-{name}.service').write_text(unit)
    run('systemctl', '--user', 'daemon-reload')
    run('systemctl', '--user', 'enable', '--now',
        *(f'{PREFIX}-{name}.service' for name in SERVICES))
    print('Demo services installed. Keep the laptop awake and connected.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'status', 'url', 'stop', 'start'))
    args = parser.parse_args()
    if args.action == 'install':
        install()
    elif args.action == 'url':
        result = run('journalctl', '--user', '-u', f'{PREFIX}-tunnel', '-n', '100',
                     '--no-pager', '-o', 'cat', capture_output=True)
        urls = re.findall(r'https://[a-z0-9-]+\.trycloudflare\.com', result.stdout)
        print(urls[-1] if urls else 'No tunnel URL yet; check service status.')
    else:
        run('systemctl', '--user', args.action,
            *(f'{PREFIX}-{name}.service' for name in SERVICES))


if __name__ == '__main__':
    main()
