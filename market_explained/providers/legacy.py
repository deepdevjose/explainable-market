"""Compatibility adapters keep the verified Yahoo/Nasdaq acquisition functions."""


class YahooDailyProvider:
    name = 'yahoo'

    def history(self, symbol: str):
        from collector import yahoo_prices
        return yahoo_prices(symbol)


class NasdaqDailyProvider:
    name = 'nasdaq'

    def history(self, symbol: str):
        from collector import nasdaq_prices
        return nasdaq_prices(symbol)
