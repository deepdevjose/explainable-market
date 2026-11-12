"""Offline provider selection, GLM parameter contracts and private response handling."""
import io
import json
import unittest
import urllib.error
from unittest.mock import patch

import ai
import config


class AIProviderTests(unittest.TestCase):
    def setUp(self):
        self.settings = patch.multiple(config,AI_PROVIDER='bigmodel',BIGMODEL_KEY='fixture-only-key',
                                       BIGMODEL_MODEL='glm-5.3-flash',DEEPSEEK_KEY='legacy-fixture-key')
        self.settings.start()

    def tearDown(self):
        self.settings.stop()

    @staticmethod
    def response(content=None,finish='stop',**extra):
        reply={'in_scope':True,'answer':'Texto educativo'} if content is None else content
        message=dict(content=json.dumps(reply),reasoning_content='Private reasoning must never be returned',**extra)
        return io.BytesIO(json.dumps({'choices':[dict(finish_reason=finish,message=message)]}).encode())

    def test_glm_uses_fixed_endpoint_enabled_thinking_and_secret_header_only(self):
        with patch('urllib.request.urlopen',return_value=self.response()) as fetch:
            result=ai.complete([{'role':'user','content':'Volatilidad'}])
        request=fetch.call_args.args[0]
        payload=json.loads(request.data)
        self.assertEqual(request.full_url,'https://open.bigmodel.cn/api/paas/v4/chat/completions')
        self.assertEqual(request.get_header('Authorization'),'Bearer fixture-only-key')
        self.assertNotIn('fixture-only-key',request.data.decode())
        self.assertEqual(payload['model'],'glm-5.3-flash')
        self.assertEqual(payload['thinking'],{'type':'enabled'})
        self.assertEqual(payload['reasoning_effort'],'low')
        self.assertEqual(payload['max_tokens'],4096)
        self.assertEqual(payload['response_format'],{'type':'json_object'})
        self.assertEqual(result,dict(in_scope=True,answer='Texto educativo'))
        self.assertNotIn('reasoning',json.dumps(result))
        self.assertNotIn('key',json.dumps(ai.provider_info()))

    def test_deepseek_contract_remains_backward_compatible(self):
        with patch.object(config,'AI_PROVIDER','deepseek'),patch('urllib.request.urlopen',return_value=self.response()) as fetch:
            ai.complete([])
        request=fetch.call_args.args[0]
        self.assertEqual(request.full_url,'https://api.deepseek.com/chat/completions')
        self.assertEqual(json.loads(request.data)['thinking'],{'type':'disabled'})
        self.assertEqual(request.get_header('Authorization'),'Bearer legacy-fixture-key')

    def test_selected_provider_errors_do_not_switch_or_fabricate_answers(self):
        error=urllib.error.HTTPError('https://open.bigmodel.cn/',401,'rejected',{},io.BytesIO(b'fixture-only-key'))
        with patch('urllib.request.urlopen',side_effect=error) as fetch:
            with self.assertRaises(ai.AIError) as result:
                ai.answer('¿Qué es volatilidad?',[],{'response_language':'es'})
        self.assertIn('BigModel',str(result.exception))
        self.assertNotIn('fixture-only-key',str(result.exception))
        self.assertEqual(fetch.call_count,1)

    def test_truncated_and_invalid_json_fail_closed(self):
        for response in (self.response(finish='length'),self.response(finish='content_filter'),
                         io.BytesIO(b'{"choices":[{"message":{"content":"not JSON"}}]}')):
            with patch('urllib.request.urlopen',return_value=response):
                with self.assertRaises(ai.AIError):ai.complete([])

    def test_missing_selected_key_uses_local_education_without_using_other_key(self):
        with patch.object(config,'BIGMODEL_KEY',''),patch('urllib.request.urlopen',side_effect=AssertionError('No network')):
            self.assertFalse(ai.configured())
            self.assertIn('sin IA generativa',ai.answer('volatilidad',[],{'response_language':'es'}))

    def test_invalid_provider_has_no_implicit_fallback(self):
        with patch.object(config,'AI_PROVIDER','unrecognized'),patch('urllib.request.urlopen',side_effect=AssertionError('No network')):
            self.assertFalse(ai.configured())
            with self.assertRaises(ai.AIError):ai.answer('volatility',[],{})

    def test_language_and_scope_guards_are_preserved(self):
        for language,expected in (('es','Responde en español.'),('en','Respond in English.'),('zh-Hans','请仅使用简体中文回答。')):
            with patch('ai.complete',return_value={'in_scope':True,'answer':'Educational answer'}) as complete:
                ai.answer('Explain volatility',[],{'response_language':language})
            self.assertIn(expected,complete.call_args.args[0][0]['content'])
        with patch('ai.complete',return_value={'in_scope':False,'answer':'Unrelated content'}):
            self.assertIn('market concepts',ai.answer('Unrelated request',[],{'response_language':'en'}))
        with patch('ai.complete',return_value={'in_scope':'true','answer':'Invalid response'}):
            with self.assertRaises(ai.AIError):
                ai.answer('Explain volatility',[],{})
