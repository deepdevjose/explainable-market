"""Common provider protocol and transparent capability/licensing metadata."""
from collections.abc import AsyncIterator
from typing import Protocol
from market_explained.markets.events import MarketEvent


class StreamingProvider(Protocol):
    name: str

    def stream(self) -> AsyncIterator[MarketEvent]: ...

    async def backfill(self) -> list[MarketEvent]: ...


CAPABILITIES = (
    {'provider':'binance', 'implemented':True, 'markets':['crypto'],
     'capabilities':['trades','ticker','1m_klines','closed_daily_backfill'],
     'credentials_required':False, 'feed':'Binance Spot; USDT quote, not USD',
     'terms':'https://www.binance.com/en/terms', 'redistribution':'Not granted by this software license; review provider terms and jurisdiction.'},
    {'provider':'yahoo', 'implemented':True, 'markets':['stocks'],
     'capabilities':['daily_history','rss_news'], 'credentials_required':False,
     'feed':'Public historical endpoints; no live entitlement',
     'terms':'https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html', 'redistribution':'Provider permission required.'},
    {'provider':'nasdaq', 'implemented':True, 'markets':['stocks'],
     'capabilities':['daily_history_fallback'], 'credentials_required':False,
     'feed':'Public historical endpoint', 'terms':'https://www.nasdaq.com/terms-of-use', 'redistribution':'Provider permission required.'},
    {'provider':'twelve_data', 'implemented':False, 'markets':['forex','indices','commodities'],
     'capabilities':[], 'credentials_required':True, 'feed':'Planned; quotas and licensing must be checked',
     'terms':'https://twelvedata.com/terms', 'redistribution':'No entitlement configured.'},
    {'provider':'alpaca', 'implemented':False, 'markets':['stocks'],
     'capabilities':[], 'credentials_required':True, 'feed':'Planned; IEX and SIP must remain distinct',
     'terms':'https://alpaca.markets/disclosures', 'redistribution':'No entitlement configured.'},
    {'provider':'fred', 'implemented':False, 'markets':['macro'],
     'capabilities':[], 'credentials_required':True, 'feed':'Planned macro series, never live spot quotes',
     'terms':'https://fred.stlouisfed.org/legal/', 'redistribution':'Series-specific restrictions apply.'},
)
