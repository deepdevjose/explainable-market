CREATE TABLE instruments (
 instrument_id TEXT PRIMARY KEY, symbol TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
 asset_class TEXT NOT NULL CHECK(asset_class IN ('stocks','forex','crypto','indices','commodities','macro')),
 base_currency TEXT, quote_currency TEXT NOT NULL, venue TEXT NOT NULL);
CREATE TABLE provider_symbols (
 provider TEXT NOT NULL, symbol TEXT NOT NULL, instrument_id TEXT NOT NULL REFERENCES instruments,
 PRIMARY KEY(provider,symbol));
CREATE TABLE stock_observations (
 ticker TEXT NOT NULL REFERENCES symbols, provider TEXT NOT NULL, date TEXT NOT NULL,
 close TEXT NOT NULL, volume TEXT NOT NULL, received_at TEXT NOT NULL,
 PRIMARY KEY(ticker,provider,date,close,volume));
CREATE TABLE market_events (
 event_id TEXT PRIMARY KEY, instrument_id TEXT NOT NULL REFERENCES instruments,
 provider TEXT NOT NULL, symbol TEXT NOT NULL, asset_class TEXT NOT NULL,
 event_type TEXT NOT NULL, event_time TEXT NOT NULL, received_at TEXT NOT NULL,
 price TEXT, bid TEXT, ask TEXT, volume TEXT, currency TEXT NOT NULL,
 source_sequence TEXT, quality_flags TEXT NOT NULL, status TEXT NOT NULL,
 payload TEXT NOT NULL);
CREATE INDEX market_events_history ON market_events(instrument_id,provider,event_time,event_id);
CREATE TABLE market_state (
 instrument_id TEXT NOT NULL REFERENCES instruments, provider TEXT NOT NULL,
 event_type TEXT NOT NULL, event_id TEXT NOT NULL REFERENCES market_events,
 event_time TEXT NOT NULL, PRIMARY KEY(instrument_id,provider,event_type));
CREATE TABLE ingestion_checkpoints (
 provider TEXT NOT NULL, stream TEXT NOT NULL, event_time TEXT NOT NULL,
 source_sequence TEXT, received_at TEXT NOT NULL, PRIMARY KEY(provider,stream));
CREATE TABLE provider_health (
 provider TEXT PRIMARY KEY, connection TEXT NOT NULL, updated_at TEXT NOT NULL,
 last_event_at TEXT, error_code TEXT, reconnects INTEGER NOT NULL DEFAULT 0);
CREATE TABLE data_quality (
 id INTEGER PRIMARY KEY, provider TEXT NOT NULL, instrument_id TEXT,
 event_id TEXT, recorded_at TEXT NOT NULL, flag TEXT NOT NULL);
CREATE TABLE model_metadata (
 model_id TEXT PRIMARY KEY, version TEXT NOT NULL, metadata TEXT NOT NULL);
CREATE TABLE prediction_history (
 prediction_id TEXT PRIMARY KEY, instrument_id TEXT NOT NULL REFERENCES instruments,
 model_id TEXT NOT NULL REFERENCES model_metadata, generated_at TEXT NOT NULL,
 data_cutoff TEXT NOT NULL, payload TEXT NOT NULL);
