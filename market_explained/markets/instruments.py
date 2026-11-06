"""Instrument identity includes venue, base asset and settlement/quote currency."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Instrument:
    instrument_id: str
    symbol: str
    name: str
    asset_class: str
    base_currency: str
    quote_currency: str
    venue: str


CRYPTO = (
    Instrument('binance:spot:BTCUSDT', 'BTCUSDT', 'Bitcoin / Tether', 'crypto', 'BTC', 'USDT', 'Binance Spot'),
    Instrument('binance:spot:ETHUSDT', 'ETHUSDT', 'Ether / Tether', 'crypto', 'ETH', 'USDT', 'Binance Spot'),
)


def resolve(provider: str, symbol: str) -> Instrument:
    for instrument in CRYPTO:
        if provider == 'binance' and symbol == instrument.symbol:
            return instrument
    raise ValueError('Unregistered provider symbol')
