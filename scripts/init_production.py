"""Generate a private VM environment once; never provision resources or print keys."""
import argparse
import os
import re
import secrets
from pathlib import Path


def initialize(host: str, target: Path) -> None:
    """Refuse malformed/injected hostnames and never overwrite an existing secret."""
    labels = host.split('.')
    if len(host) > 253 or len(labels) < 2 or not any(c.isalpha() for c in labels[-1]):
        raise ValueError('Use a public DNS hostname, without https://, path or port.')
    if any(not re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?', label) for label in labels):
        raise ValueError('Invalid public hostname.')
    target.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    content = f'PUBLIC_HOST={host.lower()}\nSECRET_KEY={secrets.token_hex(32)}\n'
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True)
    parser.add_argument('--output', type=Path, default=Path('/etc/market-explained/.env.production'))
    args = parser.parse_args()
    try:
        initialize(args.host, args.output)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Configuration not written: {exc}\n')
    print(f'Private server configuration created at {args.output}; key not displayed.')


if __name__ == '__main__':
    main()
