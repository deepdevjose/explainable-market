"""Isolated integration tests; no paid calls or network access."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ai
import app as web
import collector
import db


class MarketTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.old_path=db.DB_PATH
        db.DB_PATH=str(Path(self.tmp.name)/'test.db')
        db.init()
        web.app.config.update(TESTING=True)
        self.client=web.app.test_client()
        self.client.get('/')

    def tearDown(self):
        db.DB_PATH=self.old_path
        self.tmp.cleanup()

    def token(self,client=None):
        with (client or self.client).session_transaction() as s:
            return s['csrf']

    def post(self,path,data=None,client=None,json_body=None):
        c=client or self.client
        if json_body is not None:
            return c.post(path,json=json_body,headers={'X-CSRF-Token':self.token(c)})
        return c.post(path,data={'csrf_token':self.token(c),**(data or {})})

    def register(self,email='qa@example.test',client=None):
        response=self.post('/register',{'name':'QA','email':email,'password':'Integration!90210'},client=client)
        if response.status_code==302:
            (client or self.client).get(response.location)
        return response

    def seed_prices(self):
        # Fixtures exist only inside the temporary test database.
        with db.connect() as c:
            c.executemany('INSERT INTO prices VALUES (?,?,?,?)',[
                ('AAPL',f'2026-10-{i:02}',100+i,1000) for i in range(1,10)])
            c.execute("UPDATE symbols SET source='Verified fixture',fetched_at='2026-10-10T00:00:00+00:00' WHERE ticker='AAPL'")
            c.execute("INSERT INTO news(ticker,headline,source,url,published) VALUES ('AAPL','Revenue report','Publisher','https://example.test/news','2026-10-02T12:00:00+00:00')")

    def test_pages_work_without_data_and_never_seed_prices(self):
        for p in ['/','/app','/news','/learn','/login','/register','/symbol/AAPL']:
            self.assertEqual(self.client.get(p).status_code,200,p)
        self.assertEqual(db.q1('SELECT count(*) n FROM prices')['n'],0)
        self.assertEqual(db.q1('SELECT count(*) n FROM users')['n'],0)

    def test_registered_account_uses_hash_and_saved_watchlist(self):
        self.assertEqual(self.register().status_code,302)
        user=db.q1('SELECT * FROM users')
        self.assertNotEqual(user['password_hash'],'Integration!90210')
        self.assertTrue(user['password_hash'].startswith('scrypt:'))
        self.post('/watchlist',{'ticker':'AAPL','action':'add'})
        self.post('/watchlist',{'ticker':'AAPL','action':'add'})
        self.assertEqual(len(db.q('SELECT * FROM watchlist')),1)
        self.assertEqual(self.client.get('/watchlist').status_code,200)
        self.post('/watchlist',{'ticker':'AAPL','action':'remove'})
        self.assertFalse(db.q('SELECT * FROM watchlist'))

    def test_user_isolation(self):
        self.register()
        self.post('/watchlist',{'ticker':'AAPL','action':'add'})
        other=web.app.test_client();other.get('/')
        self.register('other@example.test',other)
        with other.session_transaction() as session:
            uid=session['user_id']
        self.assertFalse(db.q('SELECT * FROM watchlist WHERE user_id=?',(uid,)))
        self.assertNotIn('1 activos guardados',other.get('/watchlist').text)

    def test_login_and_safe_redirect(self):
        self.register();self.post('/logout');self.client.get('/login')
        r=self.post('/login?next=https://attacker.test',{'email':'QA@example.test','password':'Integration!90210'})
        self.assertEqual(r.location,'/app')
        self.client.get(r.location)
        self.post('/logout');self.client.get('/login')
        r=self.post('/login',{'email':'qa@example.test','password':'wrong'})
        self.assertIn('no son correctos',r.text)

    def test_missing_csrf_and_cross_origin_rejected(self):
        self.assertEqual(self.client.post('/api/chat',json={'message':'Hello'}).status_code,403)
        r=self.client.post('/api/chat',json={'message':'Hello'},headers={'X-CSRF-Token':self.token(),'Origin':'https://attacker.test'})
        self.assertEqual(r.status_code,403)

    def test_get_cannot_logout_or_mutate(self):
        self.register()
        self.assertEqual(self.client.get('/logout').status_code,405)
        with self.client.session_transaction() as s:self.assertIn('user_id',s)

    def test_private_watchlist_requires_login(self):
        self.assertEqual(self.client.get('/watchlist').status_code,302)
        r=self.post('/api/analyze/AAPL',json_body={})
        self.assertEqual(r.status_code,302)

    def test_chart_news_with_unknown_sentiment_and_complete_windows(self):
        self.seed_prices()
        r=self.client.get('/symbol/AAPL')
        self.assertEqual(r.status_code,200)
        self.assertIn('Revenue report',r.text)
        self.assertIn('Sin analizar',r.text)
        vals,day=web.impact(web.price_rows('AAPL'),'2026-10-02T12:00:00+00:00')
        self.assertEqual(day,'2026-10-02')
        self.assertAlmostEqual(vals[2],(108/101-1)*100)
        vals,_=web.impact(web.price_rows('AAPL'),'2026-10-09T12:00:00+00:00')
        self.assertIsNotNone(vals[0]);self.assertIsNone(vals[1]);self.assertIsNone(vals[2])
        _,next_day=web.impact(web.price_rows('AAPL'),'2026-10-02T21:00:00+00:00')
        self.assertEqual(next_day,'2026-10-03')

    def test_news_filters(self):
        self.seed_prices()
        self.assertIn('Revenue report',self.client.get('/news?ticker=AAPL').text)
        self.assertNotIn('Revenue report',self.client.get('/news?ticker=NVDA').text)
        self.assertNotIn('Revenue report',self.client.get('/news?sentiment=1').text)

    def test_export_and_api_source(self):
        self.seed_prices()
        r=self.client.get('/export/AAPL.csv')
        self.assertEqual(r.status_code,200)
        self.assertIn('ticker,date,close,volume,source',r.text)
        self.assertIn('Verified fixture',r.text)
        self.assertEqual(len(self.client.get('/api/asset/AAPL').json['prices']),9)

    def test_chat_context_is_server_owned_and_history_persists(self):
        self.seed_prices()
        with patch('ai.answer',return_value='Contexto educativo [1]') as answer:
            r=self.post('/api/chat',json_body={'message':'¿Qué veo?','ticker':'AAPL','page':'symbol_detail','context':'BUY NOW'})
        self.assertEqual(r.status_code,200)
        context=answer.call_args.args[2]
        self.assertEqual(context['asset']['close'],109)
        self.assertNotIn('BUY NOW',json.dumps(context))
        self.assertEqual(len(r.json['sources']),1)
        self.assertEqual(len(self.client.get('/api/chat').json['messages']),2)
        other=web.app.test_client();other.get('/')
        self.assertEqual(other.get('/api/chat').json['messages'],[])
        r=self.client.delete('/api/chat',headers={'X-CSRF-Token':self.token()})
        self.assertEqual(r.status_code,200)
        self.assertEqual(self.client.get('/api/chat').json['messages'],[])

    def test_ai_failure_is_truthful_and_not_saved_as_answer(self):
        with patch('ai.answer',side_effect=ai.AIError('La clave no fue aceptada.')):
            r=self.post('/api/chat',json_body={'message':'¿Qué es un activo?'})
        self.assertEqual(r.status_code,503)
        self.assertIn('clave',r.json['error'])
        self.assertFalse(db.q('SELECT * FROM messages'))

    def test_invalid_chat_and_json_rejected(self):
        for payload in ({'message':'x'*1201},{'message':[]},{'message':''},[]):
            r=self.client.post('/api/chat',json=payload,headers={'X-CSRF-Token':self.token()})
            self.assertEqual(r.status_code,400)

    def test_scope_gate_and_invalid_provider_output(self):
        with patch('ai.complete',return_value={'in_scope':False,'answer':'unrelated output'}):
            text=ai.answer('Otro tema',[],{})
            self.assertNotIn('unrelated output',text)
        with patch('ai.complete',return_value={'answer':'missing scope'}):
            with self.assertRaises(ai.AIError):ai.answer('Pregunta',[],{})

    def test_sentiment_validated_and_persisted(self):
        self.seed_prices();self.register()
        with patch('ai.complete',return_value={'items':[{'id':1,'sentiment':1,'rationale':'Tono del titular'},
                 {'id':999,'sentiment':-1,'rationale':'No existe'},{'id':1,'sentiment':7,'rationale':'Inválido'}]}):
            r=self.post('/api/analyze/AAPL',json_body={})
        self.assertEqual(r.json['analyzed'],1)
        self.assertEqual(db.q1('SELECT sentiment FROM news')['sentiment'],1)

    def test_rate_limit(self):
        for _ in range(3):self.assertTrue(db.allow('test',3,60))
        self.assertFalse(db.allow('test',3,60))

    def test_collection_failure_preserves_previous_data(self):
        self.seed_prices()
        with patch('collector.get_prices',side_effect=ValueError('provider down')),patch('collector.get_news',side_effect=OSError('feed down')):
            collector.refresh('AAPL')
        self.assertEqual(len(web.price_rows('AAPL')),9)
        row=db.q1("SELECT * FROM symbols WHERE ticker='AAPL'")
        self.assertTrue(row['price_error']);self.assertTrue(row['news_error'])

    def test_collector_idempotency_and_source_switch(self):
        self.seed_prices()
        result=([('AAPL','2026-11-01',200,1000),('AAPL','2026-11-02',202,1100)],'USD','New provider','https://example.test')
        with patch('collector.get_prices',return_value=result),patch('collector.get_news',return_value=[]):
            collector.refresh('AAPL');collector.refresh('AAPL')
        self.assertEqual(len(web.price_rows('AAPL')),2)
        self.assertIsNone(db.q1("SELECT price_error FROM symbols WHERE ticker='AAPL'")['price_error'])

    def test_security_headers_and_secret_not_exposed(self):
        import config
        for path in ['/','/app','/api/chat','/health']:
            r=self.client.get(path)
            self.assertEqual(r.headers['X-Frame-Options'],'DENY')
            self.assertIn("script-src 'self'",r.headers['Content-Security-Policy'])
            if config.DEEPSEEK_KEY:self.assertNotIn(config.DEEPSEEK_KEY,r.text)
            self.assertNotIn(config.SECRET_KEY,r.text)
        self.assertEqual(self.client.get('/.env').status_code,404)
        self.assertEqual(self.client.get('/env%20(1).txt').status_code,404)


if __name__=='__main__':
    unittest.main()
