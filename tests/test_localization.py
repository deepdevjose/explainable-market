"""Language isolation and truthful assistance without external requests."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ai
import app as web
import db
from market_explained.assistant.educational import explain
from market_explained.localization import LANGUAGES, MESSAGES, format_price


class LocalizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_path = db.DB_PATH
        db.DB_PATH = str(Path(self.tmp.name) / 'test.db')
        db.init()
        self.network = patch('collector.start', return_value=[])
        self.network.start()
        self.client = web.app.test_client()

    def tearDown(self):
        self.network.stop()
        db.DB_PATH = self.old_path
        self.tmp.cleanup()

    def test_language_persists_without_affecting_other_visitors(self):
        response = self.client.get('/markets?lang=zh-Hans')
        self.assertEqual(response.headers['Content-Language'], 'zh-Hans')
        self.assertIn('在背景中理解市场', response.text)
        self.assertIn('lang="zh-Hans"', response.text)
        self.assertIn('登录', self.client.get('/login').text)
        other = web.app.test_client()
        self.assertEqual(other.get('/').headers['Content-Language'], 'es')
        self.assertNotIn('evil', self.client.get('/?lang=evil').headers['Content-Language'])

    def test_all_pages_render_in_all_languages_without_seeded_prices(self):
        for language in LANGUAGES:
            for path in ('/', '/app', '/markets', '/market/BTCUSDT', '/sources',
                         '/learn', '/news', '/login', '/register', '/symbol/AAPL'):
                response = self.client.get(path + '?lang=' + language)
                self.assertEqual(response.status_code, 200, (language, path))
                self.assertEqual(response.headers['Content-Language'], language)
        self.assertEqual(db.q1('SELECT count(*) n FROM prices')['n'], 0)
        self.assertEqual(db.q1('SELECT count(*) n FROM market_events')['n'], 0)

    def test_catalog_complete_and_external_news_not_translated(self):
        self.assertEqual(format_price('100000.00000001'), '100.000,00000001')
        self.assertEqual(format_price('123.00000000'), '123,00')
        self.assertTrue(all(set(row) == {'en', 'zh-Hans'} and all(row.values())
                            for row in MESSAGES.values()))
        db.x("INSERT INTO news(ticker,headline,source,url,published) VALUES (?,?,?,?,?)",
             ('AAPL', 'El mercado se mueve.', 'Original publisher',
              'https://example.test/news', '2026-11-11T12:00:00+00:00'))
        response = self.client.get('/news?lang=en')
        self.assertIn('El mercado se mueve.', response.text)
        self.assertIn('Behind the headlines', response.text)
        self.assertEqual(self.client.get('/api/v1/translations').json['Mercados'], 'Markets')

    def test_missing_ai_key_is_explicit_deterministic_education(self):
        for language, keyword in (('es', 'sin IA generativa'), ('en', 'no generative AI'),
                                  ('zh-Hans', '不使用生成式')):
            with patch('config.DEEPSEEK_KEY', ''):
                result = ai.answer('volatility', [], {'response_language': language})
            self.assertIn(keyword, result)
        unknown = explain('Write a trading bot and promise returns', {'response_language': 'en'})
        self.assertIn('do not provide investment recommendations', unknown)

    def test_configured_provider_failure_does_not_masquerade_as_local_answer(self):
        with patch('config.DEEPSEEK_KEY', 'test-only-placeholder'), \
             patch('ai.complete', side_effect=ai.AIError('unavailable')):
            with self.assertRaises(ai.AIError):
                ai.answer('volatility', [], {'response_language': 'en'})
