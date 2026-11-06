"""Additive transactional migrations and SQLite online backups (WAL safe)."""
import os
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


def backup(connection: sqlite3.Connection, path: str) -> str:
    directory = Path(path).resolve().parent / 'backups'
    directory.mkdir(mode=0o700, exist_ok=True)
    fd, target = tempfile.mkstemp(prefix=Path(path).name + '-', suffix='.backup', dir=directory)
    os.close(fd)  # mkstemp creates a private 0600 file.
    try:
        with closing(sqlite3.connect(target)) as destination:
            connection.backup(destination)
    except BaseException:
        Path(target).unlink(missing_ok=True)
        raise
    return target


def migrate(connection: sqlite3.Connection, path: str) -> None:
    exists = connection.execute("SELECT 1 FROM sqlite_master WHERE name='schema_migrations'").fetchone()
    current = {r[0] for r in connection.execute('SELECT version FROM schema_migrations')} if exists else set()
    files = sorted((Path(__file__).parent / 'migrations').glob('*.sql'))
    pending = [p for p in files if p.name not in current]
    if not pending:
        return
    backup(connection, path)  # Refuse migration if the backup cannot be created.
    connection.execute('BEGIN IMMEDIATE')
    try:
        connection.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)')
        for file in pending:
            if connection.execute('SELECT 1 FROM schema_migrations WHERE version=?', (file.name,)).fetchone():
                continue  # Another process may have migrated while this process backed up.
            for statement in file.read_text().split(';'):
                if statement.strip():
                    connection.execute(statement)
            stamp = datetime.now(timezone.utc).isoformat()
            if file.name == '001_market_foundation.sql':
                connection.execute('''INSERT OR IGNORE INTO stock_observations
                    SELECT p.ticker,coalesce(s.source,'legacy:unknown'),p.date,
                    CAST(p.close AS TEXT),CAST(p.volume AS TEXT),coalesce(s.fetched_at,?)
                    FROM prices p JOIN symbols s ON s.ticker=p.ticker''', (stamp,))
                connection.execute('''INSERT INTO instruments
                    SELECT 'us:'||ticker,ticker,name,'stocks',NULL,currency,'US' FROM symbols''')
                for provider in ('yahoo', 'nasdaq'):
                    connection.execute('''INSERT INTO provider_symbols
                        SELECT ?,ticker,'us:'||ticker FROM symbols''', (provider,))
                from market_explained.markets.instruments import CRYPTO
                for instrument in CRYPTO:
                    from dataclasses import astuple
                    connection.execute('INSERT INTO instruments VALUES (?,?,?,?,?,?,?)', astuple(instrument))
                    connection.execute('INSERT INTO provider_symbols VALUES (?,?,?)',
                        ('binance', instrument.symbol, instrument.instrument_id))
            connection.execute('INSERT INTO schema_migrations VALUES (?,?)', (file.name, stamp))
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
