"""Independent optional polling worker, conservative 6/min and 600/day ceilings."""
import argparse
import logging
import signal
import threading
from datetime import datetime, timedelta

import db
from market_explained.markets.events import timestamp, utcnow
from market_explained.markets.instruments import Instrument
from market_explained.providers.twelve_data import ProviderError, TwelveDataProvider
from market_explained.storage import repository

log = logging.getLogger(__name__)


def credit() -> None:
    # Shared durable rate counters protect restarts and multiple worker instances.
    if not db.allow('twelve:day',600,86400) or not db.allow('twelve:minute',6,60):
        raise ProviderError('LOCAL_QUOTA_LIMIT')


def cycle(provider: TwelveDataProvider | None = None, *, stop: threading.Event | None = None) -> int:
    provider = provider or TwelveDataProvider()
    if not provider.key:
        repository.health(provider.name,'UNAVAILABLE','CREDENTIALS_ABSENT')
        return 0
    count = 0
    failures = 0
    for row in db.q("SELECT i.*,p.symbol provider_symbol FROM instruments i JOIN provider_symbols p USING(instrument_id) WHERE p.provider='twelve_data' ORDER BY i.symbol"):
        if stop and stop.is_set():
            break
        item = Instrument(**{k:row[k] for k in Instrument.__dataclass_fields__})
        state = db.q1('SELECT * FROM provider_instrument_status WHERE provider=? AND instrument_id=?',
                       (provider.name,item.instrument_id))
        now = utcnow()
        if state and datetime.fromisoformat(state['next_attempt_at'])>now:
            continue
        error = None
        success = False
        try:
            checkpoint = db.q1('SELECT * FROM ingestion_checkpoints WHERE provider=? AND stream=?',
                                (provider.name,row['provider_symbol']+':candle:1d'))
            if not checkpoint or (now-datetime.fromisoformat(checkpoint['received_at'])).total_seconds()>86400:
                credit()
                for event in provider.candles(item,row['provider_symbol']):
                    count += int(repository.save(event))
            if stop and stop.is_set():
                break
            credit()
            count += int(repository.save(provider.quote(item,row['provider_symbol'])))
            success = True
        except (ProviderError,ValueError,KeyError) as exc:
            error = exc.code if isinstance(exc,ProviderError) else 'INVALID_OBSERVATION'
            failures += 1
            repository.quality(provider.name,error,item.instrument_id)
            log.warning('Twelve Data %s: %s',item.symbol,error)
        delay = 900 if success else (60 if error in ('LOCAL_QUOTA_LIMIT','HTTP_429','API_429','NETWORK_OR_FORMAT_ERROR') else 86400)
        db.x('''INSERT INTO provider_instrument_status VALUES (?,?,?,?,?,?)
            ON CONFLICT(provider,instrument_id) DO UPDATE SET checked_at=excluded.checked_at,
            next_attempt_at=excluded.next_attempt_at,state=excluded.state,error_code=excluded.error_code''',
             (provider.name,item.instrument_id,timestamp(now),timestamp(now+timedelta(seconds=delay)),
              'POLLING' if success else 'UNAVAILABLE',error))
        if error=='LOCAL_QUOTA_LIMIT':
            break
    repository.health(provider.name,'DEGRADED' if failures else 'POLLING', 'INSTRUMENT_ERRORS' if failures else None)
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--once',action='store_true')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    db.init()
    stop = threading.Event()
    for sig in (signal.SIGINT,signal.SIGTERM):
        signal.signal(sig,lambda *_:stop.set())
    try:
        while not stop.is_set():
            log.info('Persisted %d Twelve Data observations',cycle(stop=stop))
            if args.once:
                break
            stop.wait(60)
    finally:
        repository.health('twelve_data','STOPPED')


if __name__=='__main__':
    main()
