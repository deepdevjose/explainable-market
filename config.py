"""Local configuration. Never export credentials to templates or logs."""
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Environment takes precedence; accept the credential file supplied with this project.
for path in (ROOT / '.env', ROOT / 'env (1).txt'):
    if path.is_file():
        for line in path.read_text().splitlines():
            key, sep, value = line.strip().partition('=')
            if sep and key and not key.startswith('#'):
                os.environ.setdefault(key.strip(), value.strip().strip('\"\''))

DATA_DIR = ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True)
secret_path = DATA_DIR / '.session-secret'
if not secret_path.exists():
    try:
        fd = os.open(secret_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            stream.write(secrets.token_hex(32))
    except FileExistsError:
        pass
SECRET_KEY = os.environ.get('SECRET_KEY') or secret_path.read_text().strip()
DEEPSEEK_KEY = os.environ.get('DEEPSEEK_API_KEY') or os.environ.get('DEEPSEEK_KEY', '')
DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-flash')
DATABASE = os.environ.get('DATABASE_PATH', str(DATA_DIR / 'market-live.db'))
