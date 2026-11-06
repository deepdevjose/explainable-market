"""Source-isolated event history and monotonic current-state projection."""
import json
from datetime import datetime

import db
from market_explained.markets.events import DataStatus, MarketEvent, timestamp, utcnow

FRESH_SECONDS = 30


def health(provider: str, connection: str, error_code: str | None = None, *, reconnect: bool = False) -> None:
    with db.connect() as c:
        c.execute('''INSERT INTO provider_health(provider,connection,updated_at,last_event_at,error_code,reconnects)
            VALUES (?,?,?,?,?,?) ON CONFLICT(provider) DO UPDATE SET connection=excluded.connection,
            updated_at=excluded.updated_at,last_event_at=coalesce(excluded.last_event_at,provider_health.last_event_at),
            error_code=excluded.error_code,reconnects=provider_health.reconnects+excluded.reconnects''',
            (provider,connection,timestamp(utcnow()),timestamp(utcnow()) if connection=='STREAMING' else None,error_code,int(reconnect)))


def quality(provider: str, flag: str, instrument_id: str | None = None, event_id: str | None = None) -> None:
    db.x('INSERT INTO data_quality(provider,instrument_id,event_id,recorded_at,flag) VALUES (?,?,?,?,?)',
         (provider,instrument_id,event_id,timestamp(utcnow()),flag))


def _older(event: MarketEvent, previous: dict) -> bool:
    if timestamp(event.event_time) != previous['event_time']:
        return timestamp(event.event_time) < previous['event_time']
    # Trades can share a millisecond. Provider sequence resolves that tie.
    if event.event_type == 'trade':
        return int(event.source_sequence) < int(previous['source_sequence'])
    return timestamp(event.received_at) < previous['received_at']


def save(event: MarketEvent) -> bool:
    with db.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        instrument = c.execute('''SELECT i.* FROM instruments i JOIN provider_symbols p
            ON p.instrument_id=i.instrument_id WHERE p.provider=? AND p.symbol=?''',
            (event.provider,event.symbol)).fetchone()
        if not instrument or (instrument['instrument_id'],instrument['asset_class'],instrument['quote_currency']) != (event.instrument_id,event.asset_class,event.currency):
            raise ValueError('Event does not match instrument registry')
        if c.execute('SELECT 1 FROM market_events WHERE event_id=?', (event.event_id,)).fetchone():
            return False
        # State is isolated by source and event type. Backfill never replaces a trade.
        state_kind = event.event_type + (':' + event.interval if event.interval else '')
        previous = c.execute('''SELECT e.* FROM market_state s JOIN market_events e USING(event_id)
            WHERE s.instrument_id=? AND s.provider=? AND s.event_type=?''',
            (event.instrument_id,event.provider,state_kind)).fetchone()
        older = previous is not None and _older(event, dict(previous))
        if older:
            event = event.flagged('OUT_OF_ORDER')
        if event.status == DataStatus.LIVE and (event.received_at-event.event_time).total_seconds() > FRESH_SECONDS:
            event = event.flagged('STALE_ON_ARRIVAL')
        payload = event.to_dict()
        c.execute('''INSERT INTO market_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (event.event_id,event.instrument_id,event.provider,event.symbol,event.asset_class,event.event_type,
             payload['event_time'],payload['received_at'],payload['price'],payload['bid'],payload['ask'],
             payload['volume'],event.currency,event.source_sequence,json.dumps(event.quality_flags),
             event.status.value,json.dumps(payload,separators=(',',':'))))
        for flag in event.quality_flags:
            c.execute('INSERT INTO data_quality(provider,instrument_id,event_id,recorded_at,flag) VALUES (?,?,?,?,?)',
                (event.provider,event.instrument_id,event.event_id,payload['received_at'],flag))
        if not older:
            c.execute('''INSERT INTO market_state VALUES (?,?,?,?,?) ON CONFLICT(instrument_id,provider,event_type)
                DO UPDATE SET event_id=excluded.event_id,event_time=excluded.event_time''',
                (event.instrument_id,event.provider,state_kind,event.event_id,payload['event_time']))
            c.execute('''INSERT INTO ingestion_checkpoints VALUES (?,?,?,?,?) ON CONFLICT(provider,stream)
                DO UPDATE SET event_time=excluded.event_time,source_sequence=excluded.source_sequence,
                received_at=excluded.received_at''',
                (event.provider,event.symbol+':'+state_kind,payload['event_time'],event.source_sequence,payload['received_at']))
        return True


def snapshot(instrument_id: str, now: datetime | None = None) -> dict:
    instrument = db.q1('SELECT * FROM instruments WHERE instrument_id=?', (instrument_id,))
    if not instrument:
        raise ValueError('Unknown instrument')
    if instrument['asset_class'] == 'stocks':
        row = db.q1('''SELECT p.*,s.source,s.fetched_at FROM prices p JOIN symbols s USING(ticker)
            WHERE ticker=? ORDER BY date DESC LIMIT 1''', (instrument['symbol'],))
        return dict(instrument=instrument, status='HISTORICAL' if row else 'UNAVAILABLE',
            observation=dict(price=str(row['close']),currency=instrument['quote_currency'],provider=row['source'],
                session_date=row['date'],event_time=None,received_at=row['fetched_at'],
                quality_flags=['LEGACY_DAILY_CLOSE_TIMESTAMP_UNKNOWN']) if row else None)
    rows = db.q('''SELECT e.payload FROM market_state s JOIN market_events e USING(event_id)
        WHERE s.instrument_id=? AND e.event_type IN ('trade','ticker','quote')
        ORDER BY e.event_time DESC,e.received_at DESC LIMIT 1''', (instrument_id,))
    if rows:
        observation = json.loads(rows[0]['payload'])
    else:
        candidates = db.q('''SELECT payload FROM market_events WHERE instrument_id=? AND event_type='candle'
            AND status='HISTORICAL' ORDER BY event_time DESC LIMIT 1''', (instrument_id,))
        observation = json.loads(candidates[0]['payload']) if candidates else None
    status = observation['status'] if observation else 'UNAVAILABLE'
    if status == 'LIVE':
        current = now or utcnow()
        provider = db.q1('SELECT * FROM provider_health WHERE provider=?', (observation['provider'],))
        ages = [(current-datetime.fromisoformat(observation[k])).total_seconds() for k in ('event_time','received_at')]
        if not provider or provider['connection'] != 'STREAMING' or max(ages) > FRESH_SECONDS:
            status = 'STALE'
    return dict(instrument=instrument,status=status,observation=observation)


def history(instrument_id: str, limit: int = 100, offset: int = 0, provider: str | None = None) -> list[dict]:
    sql = 'SELECT payload FROM market_events WHERE instrument_id=?'
    params: list = [instrument_id]
    if provider:
        sql += ' AND provider=?'
        params.append(provider)
    sql += ' ORDER BY event_time DESC,event_id DESC LIMIT ? OFFSET ?'
    return [json.loads(row['payload']) for row in db.q(sql,(*params,limit,offset))]
