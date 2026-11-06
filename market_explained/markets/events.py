"""Validated canonical contracts. Financial values stay Decimal until JSON strings."""
import hashlib
import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum


class DataStatus(str, Enum):
    LIVE = 'LIVE'
    DELAYED = 'DELAYED'
    HISTORICAL = 'HISTORICAL'
    STALE = 'STALE'
    DEMO = 'DEMO'
    UNAVAILABLE = 'UNAVAILABLE'


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def timestamp(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError('UTC timezone-aware timestamp required')
    return value.isoformat(timespec='milliseconds')


def decimal_value(value: object, *, positive: bool = True) -> Decimal:
    if isinstance(value, (bool, float)) or not isinstance(value, (str, int, Decimal)):
        raise ValueError('Financial values require decimal strings, integers or Decimal')
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('Invalid decimal') from exc
    if not result.is_finite():
        raise ValueError('Non-finite financial value')
    exponent = result.as_tuple().exponent
    if (result <= 0 if positive else result < 0) or result.adjusted() > 24 or not isinstance(exponent, int) or exponent < -24:
        raise ValueError('Invalid financial value')
    return result


@dataclass(frozen=True)
class MarketEvent:
    event_id: str
    instrument_id: str
    provider: str
    symbol: str
    asset_class: str
    event_type: str
    event_time: datetime
    received_at: datetime
    price: Decimal | None
    bid: Decimal | None
    ask: Decimal | None
    volume: Decimal | None
    currency: str
    source_sequence: str
    quality_flags: tuple[str, ...] = ()
    status: DataStatus = DataStatus.LIVE
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    interval: str | None = None
    candle_open_time: datetime | None = None
    candle_closed: bool | None = None

    def __post_init__(self) -> None:
        for field in ('event_id','instrument_id','provider','symbol','currency','source_sequence'):
            value = getattr(self, field)
            if not isinstance(value, str) or not value or len(value) > 200:
                raise ValueError('Invalid event identity')
        if self.event_type not in ('trade','ticker','quote','candle') or self.asset_class not in ('stocks','crypto','forex','indices','commodities','macro'):
            raise ValueError('Invalid market type')
        if not isinstance(self.status, DataStatus) or self.status == DataStatus.UNAVAILABLE:
            raise ValueError('An observation must have an available data status')
        timestamp(self.event_time)
        timestamp(self.received_at)
        if self.event_time > self.received_at + timedelta(seconds=5):
            raise ValueError('Event timestamp is in the future')
        for field in ('price','bid','ask','volume','open','high','low'):
            value = getattr(self, field)
            if value is not None:
                if not isinstance(value, Decimal):
                    raise ValueError('Decimal required')
                decimal_value(value, positive=field != 'volume')
        if self.price is None and (self.bid is None or self.ask is None):
            raise ValueError('Price or two-sided quote required')
        if self.bid is not None and self.ask is not None and self.bid > self.ask:
            raise ValueError('Crossed quote')
        if self.event_type == 'candle':
            if self.interval not in ('1m','1d') or type(self.candle_closed) is not bool or self.candle_open_time is None:
                raise ValueError('Candle metadata required')
            timestamp(self.candle_open_time)
            if self.candle_open_time > self.event_time or self.open is None or self.high is None or self.low is None or self.price is None:
                raise ValueError('Invalid candle window')
            if not self.low <= min(self.open,self.price) <= max(self.open,self.price) <= self.high:
                raise ValueError('Invalid OHLC bounds')
        if not isinstance(self.quality_flags, tuple) or any(not isinstance(f,str) or len(f)>80 for f in self.quality_flags):
            raise ValueError('Invalid quality flags')

    def flagged(self, flag: str) -> 'MarketEvent':
        return replace(self, quality_flags=tuple(sorted(set(self.quality_flags + (flag,)))))

    def to_dict(self) -> dict:
        result = asdict(self)
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = timestamp(value)
            elif isinstance(value, Decimal):
                result[key] = str(value)
            elif isinstance(value, DataStatus):
                result[key] = value.value
        return result


def event_id(provider: str, symbol: str, kind: str, sequence: str, values: dict) -> str:
    # Receipt time is deliberately excluded: reconnect replay must be idempotent.
    identity = json.dumps([provider, symbol, kind, sequence, values], sort_keys=True, separators=(',',':'))
    return hashlib.sha256(identity.encode()).hexdigest()
