"""Offline provider contracts, license boundaries, leakage and trained prediction APIs."""
import copy
import importlib.util
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import app as web
import db
from market_explained.ingestion.twelve_worker import cycle, credit
from market_explained.intelligence.data import latest, persist, series
from market_explained.markets.instruments import Instrument
from market_explained.providers.twelve_data import (ProviderError, TwelveDataProvider,
    normalize_candles, normalize_quote)
from market_explained.storage import repository

FIXTURE = json.loads((Path(__file__).parent/'fixtures/twelve_daily_recorded.json').read_text())
RECEIVED = datetime(2026,11,12,8,tzinfo=timezone.utc)
ITEM = Instrument('twelve:forex:EURUSD','EURUSD','Euro / US Dollar','forex','EUR','USD','Twelve Data composite')


class ProviderTests(unittest.TestCase):
    def test_recorded_daily_fixture_precision_and_open_day_exclusion(self):
        events = normalize_candles(FIXTURE,ITEM,'EUR/USD',RECEIVED)
        self.assertEqual(len(events),2)
        self.assertEqual(str(events[0].price),'1.10933')
        self.assertEqual(events[0].status.value,'HISTORICAL')
        self.assertTrue(events[0].candle_closed)
        self.assertEqual(events[0].currency,'USD')
        later = normalize_candles(FIXTURE,ITEM,'EUR/USD',RECEIVED+timedelta(seconds=3))
        self.assertEqual(events[0].event_id,later[0].event_id)
        with self.assertRaises(ValueError):
            normalize_candles(FIXTURE,ITEM,'BTC/USD',RECEIVED)

    def test_polled_quotes_are_delayed_and_require_real_timestamp(self):
        payload = dict(symbol='EUR/USD',timestamp=int(RECEIVED.timestamp())-10,close='1.1')
        event = normalize_quote(payload,ITEM,'EUR/USD',RECEIVED)
        self.assertEqual(event.status.value,'DELAYED')
        self.assertEqual(event.event_time,RECEIVED-timedelta(seconds=10))
        for field,value in (('timestamp',None),('timestamp',True),('close','NaN'),('symbol','EUR/USDT'),('currency','JPY'),('type','Common Stock')):
            with self.assertRaises(ValueError):
                normalize_quote(dict(payload,**{field:value}),ITEM,'EUR/USD',RECEIVED)

    def test_missing_credentials_never_calls_network_and_errors_are_sanitized(self):
        from io import BytesIO
        provider = TwelveDataProvider('')
        with patch('urllib.request.urlopen',side_effect=AssertionError('No network')):
            with self.assertRaisesRegex(ProviderError,'CREDENTIALS_ABSENT'):
                provider.request('quote','EUR/USD')
        provider = TwelveDataProvider('test-only-secret')
        with patch('urllib.request.urlopen',return_value=BytesIO(json.dumps(dict(status='error',code=403,message='test-only-secret')).encode())):
            with self.assertRaises(ProviderError) as result:
                provider.request('quote','EUR/USD')
        self.assertEqual(str(result.exception),'API_403')
        self.assertNotIn('secret',str(result.exception))


class StorageAndDisplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = patch.object(db,'DB_PATH',str(Path(self.tmp.name)/'test.db'))
        self.path.start()
        db.init()
        self.env = patch.dict(os.environ,{'TWELVE_DATA_PUBLIC_DISPLAY':'0'})
        self.env.start()
        self.client = web.app.test_client()

    def tearDown(self):
        self.env.stop()
        self.path.stop()
        self.tmp.cleanup()

    def test_twelve_data_reaches_local_api_but_is_hidden_on_public_routes(self):
        for event in normalize_candles(FIXTURE,ITEM,'EUR/USD',RECEIVED):
            repository.save(event)
        self.assertEqual(self.client.get('/api/v1/market/EURUSD').json['data']['status'],'HISTORICAL')
        external = {'REMOTE_ADDR':'203.0.113.10'}
        response = self.client.get('/api/v1/market/EURUSD',environ_overrides=external)
        self.assertIsNone(response.json['data']['observation'])
        for path in ('/market/EURUSD','/markets?asset_class=forex','/intelligence?symbol=EURUSD'):
            response = self.client.get(path,environ_overrides=external)
            self.assertEqual(response.status_code,200)
            self.assertNotIn('1.10933',response.text)
            self.assertIn('no está autorizada',response.text)
        for path in ('/api/v1/market/EURUSD/history','/api/v1/analysis/EURUSD','/api/v1/predictions/EURUSD'):
            self.assertEqual(self.client.get(path,environ_overrides=external).status_code,403)
        response = self.client.get('/api/v1/market/EURUSD',headers={'CF-Connecting-IP':'203.0.113.10'})
        self.assertIsNone(response.json['data']['observation'])
        with patch.dict(os.environ,{'TWELVE_DATA_PUBLIC_DISPLAY':'1'}):
            self.assertEqual(self.client.get('/api/v1/market/EURUSD',environ_overrides=external).json['data']['status'],'HISTORICAL')

    def test_polled_quotes_age_and_missing_key_is_graceful(self):
        event = normalize_quote(dict(symbol='EUR/USD',timestamp=int(RECEIVED.timestamp()),close='1.1'),ITEM,'EUR/USD',RECEIVED)
        repository.save(event)
        self.assertEqual(repository.snapshot(ITEM.instrument_id,RECEIVED)['status'],'DELAYED')
        self.assertEqual(repository.snapshot(ITEM.instrument_id,RECEIVED+timedelta(seconds=1801))['status'],'STALE')
        self.assertEqual(cycle(TwelveDataProvider('')),0)
        self.assertEqual(db.q1("SELECT error_code FROM provider_health WHERE provider='twelve_data'")['error_code'],'CREDENTIALS_ABSENT')

    def test_quota_and_plan_failures_have_durable_retry_state(self):
        provider = TwelveDataProvider('test-only-key')
        with patch.object(provider,'candles',side_effect=ProviderError('API_403')) as request:
            cycle(provider)
            self.assertEqual(request.call_count,5)
            cycle(provider)
            self.assertEqual(request.call_count,5)  # Restart does not hammer a denied instrument.
        self.assertEqual(db.q1('SELECT count(*) n FROM provider_instrument_status')['n'],5)
        with patch('db.allow',return_value=False):
            with self.assertRaisesRegex(ProviderError,'LOCAL_QUOTA_LIMIT'):
                credit()

    def test_closed_training_series_retains_revisions_without_mixing_sources(self):
        events = normalize_candles(FIXTURE,ITEM,'EUR/USD',RECEIVED)
        for event in events:
            repository.save(event)
        revised = copy.deepcopy(FIXTURE)
        revised['values'][1]['close']='1.10934'
        for event in normalize_candles(revised,ITEM,'EUR/USD',RECEIVED+timedelta(minutes=1)):
            repository.save(event)
        provider,rows = series(dict(instrument_id=ITEM.instrument_id,asset_class='forex'))
        self.assertEqual(provider,'twelve_data')
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[-1]['price'],'1.10934')
        self.assertEqual(db.q1('SELECT count(*) n FROM market_events')['n'],3)


HAS_NUMPY = importlib.util.find_spec('numpy') is not None


def training_rows():
    # Test-only generated sequence: never ingested into a running application.
    import math
    start = datetime(2025,1,1,tzinfo=timezone.utc)
    return [dict(date=(start+timedelta(days=i)).date().isoformat(),
                 cutoff=(start+timedelta(days=i+1)).isoformat(),
                 price=str(100+i*.1+math.sin(i/5))) for i in range(140)]


@unittest.skipUnless(HAS_NUMPY,'Optional forecasting dependencies not installed')
class ForecastTests(unittest.TestCase):
    setUp = StorageAndDisplayTests.setUp
    tearDown = StorageAndDisplayTests.tearDown

    def test_causal_features_and_walk_forward_ignore_future_observations(self):
        import numpy as np
        from market_explained.intelligence.forecasting import features, walk_forward
        rows = training_rows()
        prices = [float(r['price']) for r in rows]
        x,y = features(prices)
        changed = prices[:110]+[p*2 for p in prices[110:]]
        future_x,future_y = features(changed)
        np.testing.assert_array_equal(x[:80],future_x[:80])
        models = ('persistence','ridge_ar','xgboost') if importlib.util.find_spec('xgboost') else ('persistence','ridge_ar')
        for model in models:
            self.assertEqual(walk_forward(model,x,y,60,80),walk_forward(model,future_x,future_y,60,80))

    def test_real_training_protocol_prediction_persistence_and_api(self):
        from market_explained.intelligence.forecasting import generate
        rows = training_rows()
        result = generate(rows,include_xgboost=importlib.util.find_spec('xgboost') is not None)
        self.assertLess(result['evaluation_metadata']['calibration_end_session'],result['evaluation_metadata']['test_start_session'])
        self.assertEqual(result['data_cutoff_timestamp'],rows[-1]['cutoff'])
        from decimal import Decimal
        self.assertGreater(Decimal(result['uncertainty_interval']['upper_value']),Decimal(result['uncertainty_interval']['lower_value']))
        self.assertIn('persistence',result['evaluation_metadata']['held_out'])
        instrument = db.q1("SELECT * FROM instruments WHERE symbol='BTCUSDT'")
        self.assertTrue(persist(instrument,'binance',rows,result))
        self.assertFalse(persist(instrument,'binance',rows,result))
        self.assertEqual(latest(instrument['instrument_id'])['reference_price'],rows[-1]['price'])
        with patch('urllib.request.urlopen',side_effect=AssertionError('No network')):
            response = self.client.get('/api/v1/predictions/BTCUSDT')
            self.assertEqual(response.status_code,200)
            self.assertNotIn('booster_json',json.dumps(response.json))
            self.assertEqual(self.client.get('/api/v1/analysis/BTCUSDT').status_code,200)
            for language in ('es','en','zh-Hans'):
                self.assertEqual(self.client.get('/intelligence?lang='+language).status_code,200)
        self.assertEqual(db.q1('SELECT count(*) n FROM prediction_history')['n'],1)
        self.assertTrue(persist(instrument,'separate-test-provider',rows,result))
        self.assertEqual(db.q1('SELECT count(*) n FROM prediction_history')['n'],2)
        self.assertEqual(latest(instrument['instrument_id'])['provider'],'separate-test-provider')

    def test_training_rejects_small_unordered_or_invalid_data(self):
        from market_explained.intelligence.forecasting import generate
        rows = training_rows()
        for invalid in (rows[:80],list(reversed(rows)),[dict(r,price='NaN') for r in rows]):
            with self.assertRaises(ValueError):
                generate(invalid,include_xgboost=False)
