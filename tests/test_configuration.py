"""Explicit environment and fail-closed production configuration."""
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import collector

ROOT = Path(__file__).resolve().parents[1]


class ConfigurationTests(unittest.TestCase):
    def test_legacy_key_environment_alias_is_not_loaded(self):
        environment={k:v for k,v in os.environ.items() if k not in ('SECRET_KEY','DEEPSEEK_API_KEY','APP_ENV')}
        environment['DEEPSEEK_KEY']='fixture-only-not-a-real-key'
        result=subprocess.run([sys.executable,'-c',
            'import config; print(bool(config.DEEPSEEK_KEY),config.EPHEMERAL_SECRET)'],
            cwd=ROOT,env=environment,capture_output=True,text=True,check=True)
        self.assertEqual(result.stdout.strip(),'False True')

    def test_production_rejects_missing_session_key(self):
        environment={k:v for k,v in os.environ.items() if k!='SECRET_KEY'}
        environment['APP_ENV']='production'
        result=subprocess.run([sys.executable,'-c','import config'],cwd=ROOT,
            env=environment,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Production requires SECRET_KEY',result.stderr)

    def test_collector_rejects_non_provider_urls_without_io(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('Unexpected IO')):
            for url in ('file:///etc/passwd','http://api.nasdaq.com/x','https://example.test'):
                with self.assertRaises(ValueError):
                    collector.fetch(url)

    def test_rss_entities_are_rejected(self):
        from defusedxml.common import DefusedXmlException
        with patch('collector.fetch',return_value=b'<!DOCTYPE rss [<!ENTITY secret SYSTEM "file:///etc/passwd">]><rss>&secret;</rss>'):
            with self.assertRaises(DefusedXmlException):
                collector.get_news('AAPL')
