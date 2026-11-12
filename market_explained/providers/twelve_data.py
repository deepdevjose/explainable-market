"""Optional quota-bounded REST adapter. Never logs credential-bearing URLs."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Protocol

from market_explained.markets.events import DataStatus, MarketEvent, decimal_value, event_id, utcnow
from market_explained.markets.instruments import Instrument


class ProviderError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)  # Only a controlled code, never upstream messages/URLs.


class PollingProvider(Protocol):
    name: str
    def candles(self, instrument: Instrument, symbol: str) -> list[MarketEvent]: ...
    def quote(self, instrument: Instrument, symbol: str) -> MarketEvent: ...


def validate_metadata(meta: dict, instrument: Instrument, symbol: str) -> None:
    if meta.get('symbol') != symbol:
        raise ValueError('Provider symbol mismatch')
    if meta.get('currency') and meta['currency'] != instrument.quote_currency:
        raise ValueError('Provider currency mismatch')
    kind = str(meta.get('type','')).lower().replace(' ','').replace('_','')
    allowed = {'forex':{'physicalcurrency'},'commodities':{'commodity','physicalcurrency'},
               'indices':{'index'}}
    if kind and kind not in allowed.get(instrument.asset_class,set()):
        raise ValueError('Provider instrument type mismatch')


def normalize_candles(payload: dict, instrument: Instrument, symbol: str, received: datetime) -> list[MarketEvent]:
    validate_metadata(payload.get('meta',{}),instrument,symbol)
    if payload.get('meta',{}).get('interval') != '1day':
        raise ValueError('Daily candles required')
    events = []
    for row in payload.get('values', []):
        opened = datetime.strptime(row['datetime'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
        closed = opened + timedelta(days=1)
        if closed > received:
            continue  # Conservative: current UTC day is never a training candle.
        price = decimal_value(row['close'])
        events.append(MarketEvent(
            event_id('twelve_data',symbol,'candle',row['datetime'],row),
            instrument.instrument_id,'twelve_data',symbol,instrument.asset_class,'candle',
            closed,received,price,None,None,
            decimal_value(row['volume'],positive=False) if row.get('volume') is not None else None,
            instrument.quote_currency,row['datetime'],('UTC_DAY_CLOSE_CONSERVATIVE','PROVIDER_COMPOSITE'),
            DataStatus.HISTORICAL,decimal_value(row['open']),decimal_value(row['high']),
            decimal_value(row['low']),'1d',opened,True))
    return events


def normalize_quote(payload: dict, instrument: Instrument, symbol: str, received: datetime) -> MarketEvent:
    validate_metadata(payload,instrument,symbol)
    stamp = payload.get('timestamp')
    if isinstance(stamp, bool) or not isinstance(stamp, int):
        raise ValueError('Provider quote timestamp missing')
    event_time = datetime.fromtimestamp(stamp,timezone.utc)
    return MarketEvent(event_id('twelve_data',symbol,'quote',str(stamp),payload),
        instrument.instrument_id,'twelve_data',symbol,instrument.asset_class,'quote',event_time,
        received,decimal_value(payload['close']),None,None,None,instrument.quote_currency,str(stamp),
        ('POLLING_900_SECONDS','DELAY_ENTITLEMENT_UNVERIFIED','PROVIDER_COMPOSITE'),DataStatus.DELAYED)


class TwelveDataProvider:
    name = 'twelve_data'

    def __init__(self, key: str | None = None):
        self.key = key if key is not None else os.environ.get('TWELVE_DATA_API_KEY','')

    def request(self, endpoint: str, symbol: str, **params) -> dict:
        if not self.key:
            raise ProviderError('CREDENTIALS_ABSENT')
        if endpoint not in ('time_series','quote'):
            raise ValueError('Unsupported endpoint')
        query = urllib.parse.urlencode(dict(params,symbol=symbol,apikey=self.key))
        req = urllib.request.Request('https://api.twelvedata.com/' + endpoint + '?' + query,
                                     headers={'User-Agent':'ExplainableMarket/1.0'})
        try:
            # Fixed HTTPS host and allowlisted endpoint; query values are encoded.
            with urllib.request.urlopen(req,timeout=20) as response:  # nosec B310
                raw = response.read(4_000_001)
            if len(raw)>4_000_000:
                raise ProviderError('RESPONSE_TOO_LARGE')
            data = json.loads(raw)
        except urllib.error.HTTPError as exc:
            raise ProviderError('HTTP_' + str(exc.code)) from None
        except (OSError, ValueError):
            raise ProviderError('NETWORK_OR_FORMAT_ERROR') from None
        if not isinstance(data,dict):
            raise ProviderError('INVALID_RESPONSE')
        if data.get('status')=='error':
            code = data.get('code')
            raise ProviderError('API_' + str(code) if isinstance(code,int) else 'API_ERROR')
        return data

    def candles(self, instrument: Instrument, symbol: str) -> list[MarketEvent]:
        data = self.request('time_series',symbol,interval='1day',outputsize=366,timezone='UTC')
        return normalize_candles(data,instrument,symbol,utcnow())

    def quote(self, instrument: Instrument, symbol: str) -> MarketEvent:
        return normalize_quote(self.request('quote',symbol),instrument,symbol,utcnow())
