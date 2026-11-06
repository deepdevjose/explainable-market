"""Compatibility adapters keep the verified Yahoo/Nasdaq acquisition functions."""

from market_explained.providers.base import DailyHistory


class YahooDailyProvider:
    name = 'yahoo'

    def history(self, symbol: str) -> DailyHistory:
        from collector import yahoo_prices
        return yahoo_prices(symbol)


class NasdaqDailyProvider:
    name = 'nasdaq'

    def history(self, symbol: str) -> DailyHistory:
        from collector import nasdaq_prices
        return nasdaq_prices(symbol)
