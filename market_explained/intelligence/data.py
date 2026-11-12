"""Closed daily observations only. Never combine feeds or train on live candles."""
import hashlib
import json
from datetime import datetime

import db
from market_explained.markets.events import timestamp, utcnow


def series(instrument: dict) -> tuple[str,list[dict]]:
    if instrument['asset_class']=='stocks':
        source = db.q1('SELECT source FROM symbols WHERE ticker=?',(instrument['symbol'],))
        provider = source['source'] if source else None
        rows = db.q('''SELECT date,close,received_at FROM stock_observations
            WHERE ticker=? AND provider=? ORDER BY date,received_at''',(instrument['symbol'],provider))
        # Legacy dates identify sessions, not exact exchange closing timestamps.
        values = {r['date']:dict(date=r['date'],price=str(r['close']),
                  cutoff=r['date']+'T23:59:59.000+00:00') for r in rows
                  if r['date']<utcnow().date().isoformat()}
    else:
        source = db.q1('SELECT provider FROM provider_symbols WHERE instrument_id=? ORDER BY provider',
                        (instrument['instrument_id'],))
        provider = source['provider'] if source else None
        rows = db.q('''SELECT payload FROM market_events WHERE instrument_id=? AND provider=?
            AND event_type='candle' AND json_extract(payload,'$.interval')='1d'
            AND json_extract(payload,'$.candle_closed')=1 ORDER BY event_time,received_at,rowid''',
            (instrument['instrument_id'],provider))
        values = {}
        for row in rows:
            item = json.loads(row['payload'])
            if datetime.fromisoformat(item['event_time'])>utcnow():
                continue
            key = item['candle_open_time'][:10]
            values[key] = dict(date=key,price=item['price'],cutoff=item['event_time'])
    return provider or 'unknown',list(values.values())[-365:]


def digest(rows: list[dict]) -> str:
    return hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()


def latest(instrument_id: str) -> dict | None:
    row = db.q1('SELECT payload FROM prediction_history WHERE instrument_id=? ORDER BY generated_at DESC,rowid DESC LIMIT 1',
                (instrument_id,))
    if not row:
        return None
    result = json.loads(row['payload'])
    result['age_seconds'] = max(0,(utcnow()-datetime.fromisoformat(result['data_cutoff_timestamp'])).total_seconds())
    result['data_quality']['stale_daily_cutoff'] = result['age_seconds']>4*86400
    return result


def persist(instrument: dict, provider: str, rows: list[dict], result: dict) -> bool:
    version = result['model_version']
    model_id = instrument['instrument_id']+':'+provider+':'+version+':'+digest(rows)
    prediction_id = hashlib.sha256(model_id.encode()).hexdigest()
    payload = dict(result,instrument=instrument,provider=provider,dataset_sha256=digest(rows),
                   generated_at=timestamp(utcnow()),prediction_id=prediction_id)
    with db.connect() as c:
        c.execute('INSERT OR IGNORE INTO model_metadata VALUES (?,?,?)',
                  (model_id,version,json.dumps(result['model_metadata'],allow_nan=False)))
        cursor = c.execute('INSERT OR IGNORE INTO prediction_history VALUES (?,?,?,?,?,?)',
                 (prediction_id,instrument['instrument_id'],model_id,payload['generated_at'],
                  result['data_cutoff_timestamp'],json.dumps(payload,allow_nan=False)))
        return cursor.rowcount==1
