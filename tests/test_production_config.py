"""Production configuration must not leak keys, accept injection or rotate silently."""
import tempfile
import unittest
from pathlib import Path

from scripts.init_production import initialize


class ProductionConfigurationTests(unittest.TestCase):
    def test_private_key_is_stable_and_existing_config_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'private' / '.env.production'
            initialize('Market.Example.org', target)
            original = target.read_text()
            self.assertIn('PUBLIC_HOST=market.example.org\n', original)
            self.assertEqual(len(original.split('SECRET_KEY=')[1].strip()), 64)
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                initialize('market.example.org', target)
            self.assertEqual(target.read_text(), original)

    def test_rejects_host_injection_urls_and_paths_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'private' / '.env.production'
            for host in ('example.org\nSECRET_KEY=bad','https://example.org','example.org:443',
                         'example.org/path','localhost','127.0.0.1','-bad.example.org','bad..org'):
                with self.subTest(host=host), self.assertRaises(ValueError):
                    initialize(host, target)
                self.assertFalse(target.exists())
