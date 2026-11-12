"""Explicit process environment configuration; never read credential files."""
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get('DATA_DIR', str(ROOT / 'data')))
DATA_DIR.mkdir(parents=True, exist_ok=True)
PRODUCTION = os.environ.get('APP_ENV', 'development') == 'production'
SECRET_KEY = os.environ.get('SECRET_KEY', '')
if PRODUCTION and len(SECRET_KEY) < 32:
    raise RuntimeError('Production requires SECRET_KEY with at least 32 characters.')
EPHEMERAL_SECRET = not SECRET_KEY
SECRET_KEY = SECRET_KEY or secrets.token_hex(32)
DEEPSEEK_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-flash')
AI_PROVIDER = os.environ.get('AI_PROVIDER', 'deepseek').lower()
BIGMODEL_KEY = os.environ.get('BIGMODEL_API_KEY', '')
BIGMODEL_MODEL = os.environ.get('BIGMODEL_MODEL', 'glm-5.3-flash')
DATABASE = os.environ.get('DATABASE_PATH', str(DATA_DIR / 'market-live.db'))
