"""Offline contracts, provenance, lifecycle, failure isolation and API acceptance."""
import asyncio
import copy
import json
import tempfile
import unittest
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, patch

import app as web
import db
from market_explained.ingestion.workers import collect, retry_delay, run
from market_explained.markets.events import DataStatus, decimal_value
from market_explained.markets.instruments import resolve
from market_explained.providers.binance import BinanceProvider, normalize
from market_explained.storage import repository

FIXTURE = json.loads((Path(__file__).parent/'fixtures/binance.json').read_text())
RECEIVED = datetime.fromisoformat(FIXTURE['received_at'])


def trade(sequence=12345, stamp=1672531199000):
    data = {**FIXTURE['trade'],'t':sequence,'E':stamp,'T':stamp}
    return normalize(data,RECEIVED)


class ContractTests(unittest.TestCase):
    def test_decimal_precision_and_serialization(self):
        event = trade()
        self.assertEqual(event.price,Decimal('16542.12000000'))
        self.assertEqual(event.to_dict()['price'],'16542.12000000')
        self.assertTrue(event.to_dict()['event_time'].endswith('+00:00'))
        self.assertEqual(event.event_id,normalize({'data':FIXTURE['trade']},RECEIVED+timedelta(seconds=2)).event_id)

    def test_rejects_invalid_decimals_timestamps_and_identity(self):
        for value in ('NaN','Infinity','-1','0',1.2,True,'1e50','0.00000000000000000000000001'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                decimal_value(value)
        for symbol in ('BTC/USD','BTC-USD','btcusdt'):
            with self.assertRaises(ValueError):
                resolve('binance',symbol)
        with self.assertRaises(ValueError):
            resolve('yahoo','BTCUSDT')
        for replacement in ({'event_time':RECEIVED.replace(tzinfo=None)},
                            {'event_time':RECEIVED+timedelta(minutes=1)},
                            {'price':1.2}, {'bid':Decimal('2'),'ask':Decimal('1')}):
            with self.assertRaises(ValueError):
                replace(trade(),**replacement)

    def test_ticker_and_candle_contracts(self):
        ticker = normalize(FIXTURE['ticker'],RECEIVED)
        self.assertEqual(ticker.bid,Decimal('16542.11000000'))
        candle = normalize(FIXTURE['candle'],RECEIVED)
        self.assertTrue(candle.candle_closed)
        self.assertEqual(candle.interval,'1m')
        broken = copy.deepcopy(FIXTURE['candle'])
        broken['k']['l']='99999'
        with self.assertRaises(ValueError):
            normalize(broken,RECEIVED)
        broken = copy.deepcopy(FIXTURE['candle'])
        broken['k']['x']='false'
        with self.assertRaises(ValueError):
            normalize(broken,RECEIVED)

    def test_backfill_excludes_unclosed_candles(self):
        old = [1672444800000,'1','3','1','2','20',1672531199999]
        incomplete = [1672531200000,'1','3','1','2','20',1672617599999]
        from io import BytesIO
        with patch('market_explained.providers.binance.urllib.request.urlopen', return_value=BytesIO(json.dumps([old,incomplete]).encode())),patch('market_explained.providers.binance.utcnow',return_value=RECEIVED):
            events = BinanceProvider(('BTCUSDT',),2)._backfill()
        self.assertEqual(len(events),1)
        self.assertEqual(events[0].status,DataStatus.HISTORICAL)
        self.assertTrue(events[0].candle_closed)

    def test_recorded_real_stream_frames_normalize_without_network(self):
        capture=json.loads((Path(__file__).parent/'fixtures/binance_ws_recorded.json').read_text())
        events=[normalize(r['message'],datetime.fromisoformat(r['received_at'])) for r in capture['records']]
        self.assertEqual({e.event_type for e in events},{'trade','ticker','candle'})
        self.assertTrue(all(e.provider=='binance' and e.currency=='USDT' for e in events))
        self.assertFalse(next(e for e in events if e.event_type=='candle').candle_closed)

    def test_recorded_real_rest_backfill_excludes_current_day(self):
        from io import BytesIO
        capture=json.loads((Path(__file__).parent/'fixtures/binance_rest_recorded.json').read_text())
        with patch('market_explained.providers.binance.urllib.request.urlopen',return_value=BytesIO(json.dumps(capture['rows']).encode())),patch('market_explained.providers.binance.utcnow',return_value=datetime.fromisoformat(capture['recorded_at'])):
            events=BinanceProvider(('BTCUSDT',),3)._backfill()
        self.assertEqual(len(events),3)
        self.assertTrue(all(e.status==DataStatus.HISTORICAL and e.candle_closed for e in events))

    def test_backoff_is_bounded_and_jittered(self):
        with patch('market_explained.ingestion.workers.random.uniform',return_value=0.5):
            self.assertEqual(retry_delay(0),0.5)
            self.assertEqual(retry_delay(100),30)


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path_patch=patch.object(db,'DB_PATH',str(Path(self.tmp.name)/'test.db'))
        self.path_patch.start()
        db.init()
        web.app.config.update(TESTING=True)
        self.client=web.app.test_client()

    def tearDown(self):
        self.path_patch.stop()
        self.tmp.cleanup()

    def test_duplicates_ordering_and_checkpoint_are_transactional(self):
        self.assertTrue(repository.save(trade(12346)))
        self.assertFalse(repository.save(trade(12346)))
        self.assertTrue(repository.save(trade(12345)))  # Same timestamp, lower sequence.
        self.assertTrue(repository.save(trade(12344,1672531198000)))
        self.assertEqual(db.q1('SELECT count(*) n FROM market_events')['n'],3)
        self.assertEqual(db.q1('SELECT source_sequence FROM ingestion_checkpoints')['source_sequence'],'12346')
        current=repository.snapshot('binance:spot:BTCUSDT',RECEIVED)
        self.assertEqual(current['observation']['source_sequence'],'12346')
        self.assertEqual(db.q1("SELECT count(*) n FROM data_quality WHERE flag='OUT_OF_ORDER'")['n'],2)

    def test_invalid_registry_mapping_rolls_back(self):
        with self.assertRaises(ValueError):
            repository.save(replace(trade(),currency='USD'))
        self.assertEqual(db.q1('SELECT count(*) n FROM market_events')['n'],0)
        self.assertEqual(db.q1('SELECT count(*) n FROM ingestion_checkpoints')['n'],0)

    def test_freshness_historical_and_unavailable_are_distinct(self):
        self.assertEqual(repository.snapshot('binance:spot:BTCUSDT')['status'],'UNAVAILABLE')
        repository.save(trade())
        repository.health('binance','STREAMING')
        self.assertEqual(repository.snapshot('binance:spot:BTCUSDT',RECEIVED)['status'],'LIVE')
        self.assertEqual(repository.snapshot('binance:spot:BTCUSDT',RECEIVED+timedelta(seconds=40))['status'],'STALE')
        repository.health('binance','ERROR','TimeoutError')
        self.assertEqual(repository.snapshot('binance:spot:BTCUSDT',RECEIVED)['status'],'STALE')
        repository.save(replace(trade(999,1672531150000),received_at=RECEIVED))
        self.assertIn('STALE_ON_ARRIVAL',json.loads(db.q1('SELECT payload FROM market_events WHERE source_sequence=?',('999',))['payload'])['quality_flags'])
        candle=normalize(FIXTURE['candle'],RECEIVED)
        # Separate ETH instrument retains a purely historical observation.
        candle=replace(candle,instrument_id='binance:spot:ETHUSDT',symbol='ETHUSDT',status=DataStatus.HISTORICAL,event_id='historical-eth')
        repository.save(candle)
        self.assertEqual(repository.snapshot('binance:spot:ETHUSDT')['status'],'HISTORICAL')

    def test_backfill_does_not_override_trade(self):
        repository.save(trade())
        repository.save(replace(normalize(FIXTURE['candle'],RECEIVED),status=DataStatus.HISTORICAL))
        self.assertEqual(repository.snapshot('binance:spot:BTCUSDT')['observation']['event_type'],'trade')
        self.assertEqual(db.q1('SELECT count(*) n FROM market_state')['n'],2)

    def test_new_pages_and_legacy_apis_remain_available(self):
        for route in ('/markets','/markets?asset_class=crypto','/markets?asset_class=forex','/market/BTCUSDT','/sources','/health','/api/status','/api/asset/AAPL'):
            self.assertEqual(self.client.get(route).status_code,200,route)
        self.assertIn('No disponible',self.client.get('/market/BTCUSDT').text)
        self.assertIn('aún no está conectada',self.client.get('/markets?asset_class=forex').text)
        with self.client.get('/static/style.css') as response:
            self.assertIn('IBM Plex Sans',response.text)
        self.assertEqual(self.client.get('/market/AAPL').location,'/symbol/AAPL')

    def test_paginated_typed_errors_and_provider_status(self):
        response=self.client.get('/api/v1/instruments?asset_class=crypto&limit=1&offset=1').json
        self.assertEqual(len(response['data']),1)
        self.assertEqual(response['pagination']['total'],2)
        self.assertEqual(self.client.get('/api/v1/instruments?q=Bitcoin').json['data'][0]['symbol'],'BTCUSDT')
        for route in ('/api/v1/instruments?limit=999','/api/v1/instruments?offset=-1','/api/v1/instruments?limit=x','/api/v1/instruments?asset_class=wrong'):
            r=self.client.get(route)
            self.assertEqual(r.status_code,400)
            self.assertIn('code',r.json['error'])
        self.assertEqual(self.client.get('/api/v1/market/BTC-USD').status_code,404)
        self.assertEqual(self.client.get('/api/v1/predictions/BTCUSDT').status_code,501)
        providers=self.client.get('/api/v1/providers/status').json['data']
        self.assertFalse(next(p for p in providers if p['provider']=='alpaca')['implemented'])
        self.assertEqual(self.client.get('/api/v1/system/health').json['status'],'ok')

    def test_persisted_events_reach_user_without_upstream_requests(self):
        repository.save(trade())
        with patch('urllib.request.urlopen',side_effect=AssertionError('No external request in read API')):
            r=self.client.get('/api/v1/market/BTCUSDT')
            self.assertEqual(r.json['data']['status'],'STALE')
            observation=r.json['data']['observation']
            self.assertEqual(observation['price'],'16542.12000000')
            self.assertEqual(observation['provider'],'binance')
            self.assertTrue(observation['event_time'].endswith('+00:00'))
            self.assertIn('16542.12000000',self.client.get('/market/BTCUSDT').text)
            self.assertEqual(len(self.client.get('/api/v1/market/BTCUSDT/history?limit=1').json['data']),1)

    def test_crypto_assistant_context_is_server_owned_and_source_labeled(self):
        repository.save(trade())
        self.client.get('/market/BTCUSDT')
        with self.client.session_transaction() as session:
            token=session['csrf']
        with patch('ai.answer',return_value='Explicación educativa') as answer:
            response=self.client.post('/api/chat',json={'message':'¿Qué significa USDT?',
                'ticker':'BTCUSDT','page':'markets.detail','context':'Invented price'},
                headers={'X-CSRF-Token':token})
        self.assertEqual(response.status_code,200)
        context=answer.call_args.args[2]
        self.assertEqual(context['asset']['currency'],'USDT')
        self.assertEqual(context['asset']['source'],'binance')
        self.assertEqual(context['asset']['status'],'STALE')
        self.assertNotIn('Invented price',json.dumps(context))

    def test_v1_rate_limit_contract(self):
        with patch('db.allow',return_value=False):
            response=self.client.get('/api/v1/markets')
        self.assertEqual(response.status_code,429)
        self.assertEqual(response.headers['Retry-After'],'60')
        self.assertEqual(response.json['error']['code'],'rate_limited')


class WorkerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path_patch=patch.object(db,'DB_PATH',str(Path(self.tmp.name)/'worker.db'))
        self.path_patch.start()
        db.init()

    async def asyncTearDown(self):
        self.path_patch.stop()
        self.tmp.cleanup()

    async def test_reconnect_resubscribe_and_normalize_via_local_websocket(self):
        from websockets.asyncio.server import serve
        paths=[]
        async def handler(socket):
            paths.append(socket.request.path)
            await socket.send(json.dumps(FIXTURE['trade']))
            await socket.close()
        async with serve(handler,'127.0.0.1',0) as server:
            port=server.sockets[0].getsockname()[1]
            queue=asyncio.Queue(maxsize=1)
            with patch('market_explained.providers.binance.WS_URL',f'ws://127.0.0.1:{port}/stream?streams='),patch('market_explained.providers.binance.utcnow',return_value=RECEIVED),patch('market_explained.ingestion.workers.retry_delay',return_value=0.001):
                task=asyncio.create_task(collect(BinanceProvider(('BTCUSDT',)),queue))
                try:
                    first=await asyncio.wait_for(queue.get(),3)
                    second=await asyncio.wait_for(queue.get(),3)
                    self.assertEqual(first.event_id,second.event_id)
                    self.assertEqual(len(paths),2)
                    self.assertIn('btcusdt@kline_1m',paths[0])
                    self.assertEqual(paths[0],paths[1])
                finally:
                    task.cancel()
                    await asyncio.gather(task,return_exceptions=True)

    async def test_connection_rotation_before_provider_limit(self):
        socket=AsyncMock()
        socket.recv.side_effect=asyncio.TimeoutError
        @asynccontextmanager
        async def connect(*args,**kwargs):
            self.assertEqual(kwargs['ping_interval'],20)
            self.assertEqual(kwargs['max_queue'],16)
            yield socket
        with patch('websockets.asyncio.client.connect',connect),patch('market_explained.providers.binance.ROTATE_SECONDS',0):
            self.assertEqual([e async for e in BinanceProvider().stream()],[])
        socket.recv.assert_not_called()

    async def test_graceful_shutdown_drains_bounded_queue_despite_rest_failure(self):
        stop=asyncio.Event()
        class FakeProvider:
            name='binance'
            async def stream(self):
                for i in range(10):
                    yield trade(20000+i)
                stop.set()
                await asyncio.Future()
            async def backfill(self):
                raise OSError('REST down')
        await asyncio.wait_for(run([FakeProvider()],stop,queue_size=1),5)
        self.assertEqual(db.q1('SELECT count(*) n FROM market_events')['n'],10)
        self.assertEqual(db.q1('SELECT source_sequence FROM ingestion_checkpoints')['source_sequence'],'20009')
        self.assertEqual(db.q1('SELECT connection FROM provider_health')['connection'],'STOPPED')
        self.assertTrue(db.q("SELECT * FROM data_quality WHERE flag='BACKFILL_FAILED:OSError'"))

    async def test_provider_failures_are_isolated(self):
        stop=asyncio.Event()
        class Down:
            name='unavailable-test-provider'
            async def stream(self):
                raise OSError('offline')
                yield  # async generator contract
            async def backfill(self):
                return []
        class Healthy:
            name='binance'
            async def stream(self):
                yield trade()
                stop.set()
                await asyncio.Future()
            async def backfill(self):
                return []
        await asyncio.wait_for(run([Down(),Healthy()],stop,queue_size=1),5)
        self.assertEqual(db.q1('SELECT count(*) n FROM market_events')['n'],1)

    async def test_storage_failure_is_surfaced_and_worker_stops(self):
        import sqlite3
        stop=asyncio.Event()
        class Feed:
            name='binance'
            async def stream(self):
                yield trade()
                await asyncio.Future()
            async def backfill(self):
                return []
        with patch('market_explained.storage.repository.save',side_effect=sqlite3.IntegrityError('invalid storage')):
            with self.assertRaises(sqlite3.IntegrityError):
                await asyncio.wait_for(run([Feed()],stop,queue_size=1),3)
        self.assertEqual(db.q1('SELECT connection FROM provider_health')['connection'],'STOPPED')
