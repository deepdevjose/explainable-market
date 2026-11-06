"""Public Binance Spot data only. No API keys, accounts, orders or trading methods."""
import asyncio
import json
import time
import urllib.parse
import urllib.request
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from decimal import Decimal

from market_explained.markets.events import DataStatus, MarketEvent, decimal_value, event_id, utcnow
from market_explained.markets.instruments import resolve

WS_URL = 'wss://data-stream.binance.vision:443/stream?streams='
REST_URL = 'https://data-api.binance.vision/api/v3/klines'
ROTATE_SECONDS = 23 * 3600 + 50 * 60


def from_ms(value: object) -> datetime:
    if type(value) is not int or value < 0:
        raise ValueError('Integer millisecond timestamp required')
    return datetime.fromtimestamp(value / 1000, timezone.utc)


def normalize(message: dict, received_at: datetime | None = None) -> MarketEvent:
    data = message.get('data', message)
    instrument = resolve('binance', data['s'])
    kind = {'trade':'trade', '24hrTicker':'ticker', 'kline':'candle'}.get(data['e'])
    if kind is None:
        raise ValueError('Unsupported Binance event')
    received = received_at or utcnow()
    stamp = from_ms(data['T'] if kind == 'trade' else data['E'])
    fields: dict = {}
    bid = ask = None
    if kind == 'trade':
        if type(data['t']) is not int or data['t'] < 0:
            raise ValueError('Invalid trade sequence')
        price, volume, sequence = data['p'], data['q'], str(data['t'])
        identity = {}  # A trade ID identifies one immutable observation.
    elif kind == 'ticker':
        price, volume, sequence = data['c'], data['v'], str(data['E'])
        bid, ask = decimal_value(data['b']), decimal_value(data['a'])
        identity = data
    else:
        candle = data['k']
        if candle['s'] != data['s']:
            raise ValueError('Candle symbol mismatch')
        price, volume = candle['c'], candle['v']
        sequence = f"{candle['i']}:{candle['t']}:{data['E']}:{candle['x']}"
        fields = dict(open=decimal_value(candle['o']), high=decimal_value(candle['h']),
            low=decimal_value(candle['l']), interval=candle['i'],
            candle_open_time=from_ms(candle['t']), candle_closed=candle['x'])
        identity = candle
    return MarketEvent(event_id('binance',instrument.symbol,kind,sequence,identity),
        instrument.instrument_id,'binance',instrument.symbol,'crypto',kind,stamp,received,
        decimal_value(price),bid,ask,decimal_value(volume,positive=False),'USDT',sequence,**fields)


class BinanceProvider:
    name = 'binance'

    def __init__(self, symbols: tuple[str, ...] = ('BTCUSDT','ETHUSDT'), backfill_days: int = 365):
        if not symbols or len(set(symbols)) != len(symbols):
            raise ValueError('Select unique registered symbols')
        for symbol in symbols:
            resolve(self.name, symbol)
        if not 1 <= backfill_days <= 365:
            raise ValueError('Backfill must be between 1 and 365 days')
        self.symbols = symbols
        self.backfill_days = backfill_days

    async def stream(self) -> AsyncIterator[MarketEvent]:
        from websockets.asyncio.client import connect
        streams = '/'.join(f'{s.lower()}@{kind}' for s in self.symbols for kind in ('trade','ticker','kline_1m'))
        # websockets automatically answers server ping frames with matching pong payloads.
        async with connect(WS_URL + streams, ping_interval=20, ping_timeout=20,
                           open_timeout=15, close_timeout=5, max_queue=16, max_size=1_000_000) as socket:
            deadline = time.monotonic() + ROTATE_SECONDS
            while time.monotonic() < deadline:
                remaining = deadline - time.monotonic()
                try:
                    async with asyncio.timeout(min(60, remaining)):
                        raw = await socket.recv()
                except TimeoutError:
                    if time.monotonic() >= deadline:
                        return
                    raise TimeoutError('No market messages for 60 seconds') from None
                message = json.loads(raw, parse_float=Decimal)
                yield normalize(message)

    def _backfill(self) -> list[MarketEvent]:
        events = []
        received = utcnow()
        for symbol in self.symbols:
            query = urllib.parse.urlencode({'symbol':symbol, 'interval':'1d', 'limit':self.backfill_days + 1})
            request = urllib.request.Request(REST_URL + '?' + query, headers={'User-Agent':'MarketExplained/2'})
            # fixed HTTPS market-data endpoint; symbols come from registry.
            with urllib.request.urlopen(request, timeout=18) as response:  # nosec B310
                rows = json.load(response, parse_float=Decimal)
            for row in rows:
                if from_ms(row[6]) >= received:
                    continue  # Never backfill an incomplete daily candle.
                data = {'e':'kline','E':row[6],'s':symbol,'k':{'s':symbol,'t':row[0],'i':'1d',
                    'o':row[1],'h':row[2],'l':row[3],'c':row[4],'v':row[5],'x':True}}
                event = normalize(data, received)
                # Deterministic ID also matches re-fetches; receipt is never identity.
                from dataclasses import replace
                events.append(replace(event,status=DataStatus.HISTORICAL))
        return events

    async def backfill(self) -> list[MarketEvent]:
        return await asyncio.to_thread(self._backfill)
