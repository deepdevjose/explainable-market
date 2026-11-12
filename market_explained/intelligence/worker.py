"""Train outside Flask; persist reproducible forecasts, models and evaluations."""
import argparse
import logging
import signal
import threading

import db
from market_explained.intelligence.data import digest, latest, persist, series
from market_explained.intelligence.forecasting import generate, VERSION
from market_explained.storage import repository

log = logging.getLogger(__name__)


def cycle(stop: threading.Event | None = None) -> int:
    count = 0
    failures = 0
    for instrument in db.q('SELECT * FROM instruments ORDER BY symbol'):
        if stop and stop.is_set():
            break
        provider,rows = series(instrument)
        previous = latest(instrument['instrument_id'])
        if previous and previous['provider']==provider and previous['dataset_sha256']==digest(rows) and previous['model_version']==VERSION:
            continue
        if len(rows)<120:
            continue
        try:
            result = generate(rows)
            count += int(persist(instrument,provider,rows,result))
            log.info('%s: %s, %d closed observations',instrument['symbol'],result['model'],len(rows))
        except (ValueError,ArithmeticError) as exc:
            failures += 1
            log.warning('%s: training failed (%s)',instrument['symbol'],type(exc).__name__)
    repository.health('forecasting','DEGRADED' if failures else 'READY', 'MODEL_ERRORS' if failures else None)
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
    while not stop.is_set():
        log.info('Generated %d forecasts',cycle(stop))
        if args.once:
            break
        stop.wait(1800)


if __name__=='__main__':
    main()
