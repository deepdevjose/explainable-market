"""Protect publication boundaries using disposable Git indexes and fake credentials."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.check_repository_hygiene import check, content_issue, path_issue


class RepositoryHygieneTests(unittest.TestCase):
    def test_example_rejects_quoted_unquoted_and_nonprefixed_credentials(self):
        self.assertIsNone(content_issue('.env.example',b'AI_PROVIDER=bigmodel\nBIGMODEL_API_KEY=\n'))
        for key in ('DEEPSEEK_API_KEY','BIGMODEL_API_KEY','TWELVE_DATA_API_KEY','SECRET_KEY'):
            for value in ('a'*32,'"'+'a'*32+'"'):
                self.assertIsNotNone(content_issue('.env.example',f'{key}={value}\n'.encode()))

    def test_exact_index_is_scanned_even_after_working_copy_is_sanitized(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            subprocess.run(['git','init','-q',folder],check=True)
            example=root/'.env.example'
            field='BIGMODEL_API_KEY'
            example.write_text(field+'='+'a'*32+'\n')
            subprocess.run(['git','add','.env.example'],cwd=root,check=True)
            example.write_text('BIGMODEL_API_KEY=\n')
            self.assertEqual(check(root),[])
            self.assertEqual(check(root,staged=True)[0][0],'.env.example')
            subprocess.run(['git','add','.env.example'],cwd=root,check=True)
            self.assertEqual(check(root,staged=True),[])
            # Newly created untracked files are checked before they can be staged.
            (root/'accidental.txt').write_text('BIGMODEL_API_KEY="'+'a'*32+'"')
            self.assertEqual(check(root)[0][0],'accidental.txt')

    def test_provider_tokens_and_private_keys_are_found_without_revealing_values(self):
        for data in (b'sk-'+b'a'*32,b'a'*32+b'.'+b'B'*16,
                     b'-----BEGIN '+b'PRIVATE KEY-----',b'ghp_'+b'a'*36,
                     b'BIGMODEL_API_KEY="'+b'a'*32+b'"'):
            reason=content_issue('notes.txt',data)
            self.assertIsNotNone(reason)
            self.assertNotIn(data.decode(),reason)
        self.assertIsNone(content_issue('tests/test_example.py',b'BIGMODEL_KEY="fixture-only-key"'))
        self.assertIsNotNone(content_issue('settings.py',b'BIGMODEL_KEY="fixture-only-key"'))

    def test_private_paths_are_rejected_and_public_assets_are_allowed(self):
        for path in ('data/users.db','nested/.env','server.env','keys/client.pem',
                     'credentials-private.json','output/playwright/screenshot.png',
                     '.playwright-cli/session.json','Checkpoint2.pdf'):
            self.assertIsNotNone(path_issue(path),path)
        for path in ('.env.example','static/mark.svg','static/fonts/plex.woff2','tests/fixtures/binance.json'):
            self.assertIsNone(path_issue(path),path)
