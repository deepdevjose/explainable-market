# Offline market captures

The Binance `*_recorded.json` files contain public API responses captured during
integration checks. `binance.json` is the original contract fixture.

`twelve_daily_recorded.json` contains the three EUR/USD daily rows returned by
Twelve Data on 2026-11-12. Authentication was supplied by the private server
environment; there are no credentials in this response fixture. The test fixes its
receipt time and checks that the still-open UTC day is excluded.

Fixtures are used only by tests. Production workers request their own real data;
fixtures are never loaded as live observations. Generated model test series remain
in memory/temporary test databases. These files do not grant third-party data
redistribution rights beyond the provider's terms.
