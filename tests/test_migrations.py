"""Upgrade real legacy schemas without losing user-owned data."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import collector
import db
from market_explained.storage.database import migrate


class MigrationTests(unittest.TestCase):
    def test_upgrade_preserves_legacy_rows_and_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / 'legacy.db')
            with patch.object(db, 'DB_PATH', path):
                with db.connect() as c:
                    c.executescript(db.SCHEMA)
                    c.execute("INSERT INTO symbols(ticker,name,sector,source) VALUES ('AAPL','Apple','Tech','Old feed')")
                    c.execute("INSERT INTO users VALUES (7,'person@example.test','hash','Person','2026-01-01')")
                    c.execute("INSERT INTO watchlist VALUES (7,'AAPL','2026-01-01')")
                    c.execute("INSERT INTO messages VALUES (1,'user:7','user','Question','2026-01-01')")
                    c.execute("INSERT INTO prices VALUES ('AAPL','2026-01-01',123.45,10)")
                    c.execute("INSERT INTO news(ticker,headline,source,url,published) VALUES ('AAPL','Title','Source','https://example.test','2026-01-01')")
                before = {t: db.q('SELECT * FROM ' + t) for t in ('users','watchlist','messages','prices','news')}
                db.init()
                db.init()
                for table, rows in before.items():
                    self.assertEqual(db.q('SELECT * FROM ' + table), rows)
                self.assertEqual(db.q1('SELECT count(*) n FROM schema_migrations')['n'], 3)
                self.assertEqual(db.q1('SELECT count(*) n FROM stock_observations')['n'], 1)
                backups = list((Path(tmp) / 'backups').glob('*.backup'))
                self.assertEqual(len(backups), 1)
                self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)
                restored = sqlite3.connect(backups[0])
                try:
                    self.assertEqual(restored.execute('SELECT count(*) FROM watchlist').fetchone()[0], 1)
                    self.assertEqual(restored.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                finally:
                    restored.close()
                result = ([('AAPL','2026-01-02',200,20)],'USD','New feed','https://example.test')
                with patch('collector.get_prices', return_value=result), patch('collector.get_news', return_value=[]):
                    collector.refresh('AAPL')
                self.assertEqual(db.q1('SELECT count(*) n FROM stock_observations')['n'], 2)
                self.assertEqual(db.q1('SELECT provider FROM stock_observations WHERE date=?', ('2026-01-01',))['provider'], 'Old feed')
                self.assertEqual(db.q1('SELECT count(*) n FROM watchlist')['n'], 1)

    def test_backup_failure_prevents_migration(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / 'legacy.db')
            with patch.object(db, 'DB_PATH', path), db.connect() as c:
                c.executescript(db.SCHEMA)
                with patch('market_explained.storage.database.backup', side_effect=OSError('disk full')):
                    with self.assertRaises(OSError):
                        migrate(c, path)
                self.assertIsNone(c.execute("SELECT name FROM sqlite_master WHERE name='market_events'").fetchone())
