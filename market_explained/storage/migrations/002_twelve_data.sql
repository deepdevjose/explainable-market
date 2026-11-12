INSERT INTO instruments VALUES
('twelve:forex:EURUSD','EURUSD','Euro / US Dollar','forex','EUR','USD','Twelve Data composite'),
('twelve:forex:USDJPY','USDJPY','US Dollar / Japanese Yen','forex','USD','JPY','Twelve Data composite'),
('twelve:index:SPX','SPX','S&P 500 Index','indices',NULL,'USD','Twelve Data index'),
('twelve:metal:XAUUSD','XAUUSD','Gold / US Dollar','commodities','XAU','USD','Twelve Data composite');
INSERT INTO provider_symbols VALUES
('twelve_data','EUR/USD','twelve:forex:EURUSD'),
('twelve_data','USD/JPY','twelve:forex:USDJPY'),
('twelve_data','SPX','twelve:index:SPX'),
('twelve_data','XAU/USD','twelve:metal:XAUUSD');
CREATE TABLE provider_instrument_status (
 provider TEXT NOT NULL, instrument_id TEXT NOT NULL REFERENCES instruments(instrument_id),
 checked_at TEXT NOT NULL, next_attempt_at TEXT NOT NULL, state TEXT NOT NULL, error_code TEXT,
 PRIMARY KEY(provider,instrument_id)
);
CREATE INDEX predictions_lookup ON prediction_history(instrument_id,generated_at DESC);
