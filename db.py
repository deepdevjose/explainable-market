"""Persistent, real-source data. The old prototype database is never imported."""
import sqlite3
import os
from contextlib import contextmanager
import config

DB_PATH = config.DATABASE
CATALOG = [
 ('AAPL','Apple','Tecnología'), ('MSFT','Microsoft','Tecnología'),
 ('NVDA','NVIDIA','Semiconductores'), ('GOOGL','Alphabet','Comunicación'),
 ('AMZN','Amazon','Consumo'), ('META','Meta Platforms','Comunicación'),
 ('TSLA','Tesla','Automoción'), ('AMD','Advanced Micro Devices','Semiconductores'),
 ('JPM','JPMorgan Chase','Finanzas'), ('V','Visa','Finanzas'),
 ('XOM','Exxon Mobil','Energía'), ('SPY','SPDR S&P 500 ETF','Índice · ETF'),
]
SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
 password_hash TEXT NOT NULL, name TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS symbols (
 ticker TEXT PRIMARY KEY, name TEXT NOT NULL, sector TEXT NOT NULL,
 currency TEXT NOT NULL DEFAULT 'USD', source TEXT, source_url TEXT,
 fetched_at TEXT, last_attempt TEXT, price_error TEXT, news_error TEXT);
CREATE TABLE IF NOT EXISTS prices (
 ticker TEXT NOT NULL REFERENCES symbols(ticker), date TEXT NOT NULL,
 close REAL NOT NULL CHECK(close>0), volume REAL NOT NULL,
 PRIMARY KEY(ticker,date));
CREATE TABLE IF NOT EXISTS news (
 id INTEGER PRIMARY KEY, ticker TEXT NOT NULL REFERENCES symbols(ticker),
 headline TEXT NOT NULL, source TEXT NOT NULL, url TEXT NOT NULL,
 published TEXT NOT NULL, sentiment INTEGER, rationale TEXT,
 analyzed_at TEXT, UNIQUE(ticker,url));
CREATE TABLE IF NOT EXISTS watchlist (
 user_id INTEGER NOT NULL REFERENCES users(id), ticker TEXT NOT NULL REFERENCES symbols(ticker),
 added_at TEXT NOT NULL, PRIMARY KEY(user_id,ticker));
CREATE TABLE IF NOT EXISTS messages (
 id INTEGER PRIMARY KEY, owner TEXT NOT NULL, role TEXT NOT NULL,
 content TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS rate_limits (
 bucket TEXT PRIMARY KEY, start INTEGER NOT NULL, hits INTEGER NOT NULL);
'''

@contextmanager
def connect():
    # Restrict new database files before SQLite creates WAL/SHM beside them.
    if DB_PATH != ':memory:':
        fd = os.open(DB_PATH, os.O_WRONLY | os.O_CREAT, 0o600)
        os.close(fd)
        os.chmod(DB_PATH, 0o600)
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init():
    with connect() as c:
        c.execute('PRAGMA journal_mode=WAL')
        c.executescript(SCHEMA)
        c.executemany('INSERT OR IGNORE INTO symbols(ticker,name,sector) VALUES (?,?,?)', CATALOG)
        c.commit()
        from market_explained.storage.database import migrate
        migrate(c, DB_PATH)

def q(sql, params=()):
    with connect() as c:
        return [dict(r) for r in c.execute(sql, params).fetchall()]

def q1(sql, params=()):
    rows=q(sql,params)
    return rows[0] if rows else None

def x(sql, params=()):
    with connect() as c:
        return c.execute(sql,params).lastrowid

def allow(bucket, limit, period):
    import time
    now=int(time.time())
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        c.execute('DELETE FROM rate_limits WHERE start < ?', (now-86400,))
        row=c.execute('SELECT * FROM rate_limits WHERE bucket=?',(bucket,)).fetchone()
        if not row or now-row['start'] >= period:
            c.execute('INSERT OR REPLACE INTO rate_limits VALUES (?,?,1)',(bucket,now))
            return True
        if row['hits'] >= limit:
            return False
        c.execute('UPDATE rate_limits SET hits=hits+1 WHERE bucket=?',(bucket,))
        return True
