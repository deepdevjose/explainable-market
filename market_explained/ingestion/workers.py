"""Async provider isolation, bounded backpressure and durable per-source checkpoints."""
import argparse
import asyncio
import logging
import random
import signal
import sqlite3
import time

import db
from market_explained.markets.events import MarketEvent
from market_explained.providers.base import StreamingProvider
from market_explained.providers.binance import BinanceProvider
from market_explained.storage import repository

LOG = logging.getLogger(__name__)


def retry_delay(attempt: int) -> float:
    return random.uniform(0.5, 1.0) * min(60, 2 ** min(attempt, 6))


async def persist(queue: asyncio.Queue) -> None:
    while True:
        event = await queue.get()
        try:
            if event is None:
                return
            for attempt in range(5):
                try:
                    await asyncio.to_thread(repository.save, event)
                    break
                except sqlite3.OperationalError as exc:
                    if exc.sqlite_errorcode not in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) or attempt == 4:
                        raise  # Fail closed: never acknowledge a write that was lost.
                    await asyncio.sleep(retry_delay(attempt))
        finally:
            queue.task_done()


async def collect(provider: StreamingProvider, queue: asyncio.Queue) -> None:
    attempt = 0
    while True:
        started = time.monotonic()
        await asyncio.to_thread(repository.health, provider.name, 'CONNECTING')
        try:
            async for event in provider.stream():
                await queue.put(event)  # Bounded queue applies backpressure; no silent drops.
                await asyncio.to_thread(repository.health, provider.name, 'STREAMING')
            await asyncio.to_thread(repository.quality, provider.name, 'CONNECTION_ROTATED')
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            # Exception text can contain upstream payloads/URLs. Store only its class.
            code = type(exc).__name__
            LOG.warning('%s stream unavailable: %s', provider.name, code)
            await asyncio.to_thread(repository.health, provider.name, 'ERROR', code, reconnect=True)
            await asyncio.to_thread(repository.quality, provider.name, 'STREAM_GAP:' + code)
        if time.monotonic() - started > 30:
            attempt = 0
        await asyncio.sleep(retry_delay(attempt))
        attempt += 1


async def backfill(provider: StreamingProvider, queue: asyncio.Queue) -> None:
    # Retry independently: a REST outage must not prevent the stream from connecting.
    for attempt in range(5):
        try:
            for event in await provider.backfill():
                await queue.put(event)
            return
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            code = type(exc).__name__
            LOG.warning('%s backfill unavailable: %s', provider.name, code)
            await asyncio.to_thread(repository.quality, provider.name, 'BACKFILL_FAILED:' + code)
            if attempt < 4:
                await asyncio.sleep(retry_delay(attempt))


async def run(providers: list[StreamingProvider], stop: asyncio.Event, *, queue_size: int = 1000) -> None:
    if queue_size < 1:
        raise ValueError('Queue must be bounded and positive')
    queue: asyncio.Queue[MarketEvent | None] = asyncio.Queue(maxsize=queue_size)
    consumer = asyncio.create_task(persist(queue), name='sqlite-writer')
    tasks = [asyncio.create_task(task(provider, queue)) for provider in providers for task in (collect,backfill)]
    stopping = asyncio.create_task(stop.wait())
    try:
        done, _ = await asyncio.wait([consumer,stopping,*tasks], return_when=asyncio.FIRST_COMPLETED)
        # A completed backfill is expected; continue monitoring remaining tasks.
        while stopping not in done and consumer not in done:
            for task in done:
                task.result()
            tasks = [t for t in tasks if not t.done()]
            done, _ = await asyncio.wait([consumer,stopping,*tasks], return_when=asyncio.FIRST_COMPLETED)
        if consumer in done:
            await consumer  # Surface storage failure and terminate instead of dropping data.
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        try:
            if not consumer.done():
                drained = asyncio.create_task(queue.join())
                try:
                    done, _ = await asyncio.wait([consumer,drained],timeout=30,
                                                 return_when=asyncio.FIRST_COMPLETED)
                    if consumer in done:
                        await consumer
                    elif drained in done:
                        await queue.put(None)
                        await consumer
                    else:
                        raise TimeoutError('Worker could not drain pending events within 30 seconds')
                finally:
                    drained.cancel()
                    await asyncio.gather(drained,return_exceptions=True)
        finally:
            if not consumer.done():
                consumer.cancel()
            stopping.cancel()
            await asyncio.gather(consumer,stopping,return_exceptions=True)
            for provider in providers:
                await asyncio.to_thread(repository.health, provider.name, 'STOPPED')


async def main_async(args: argparse.Namespace) -> None:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for name in (signal.SIGINT,signal.SIGTERM):
        loop.add_signal_handler(name, stop.set)
    if args.duration:
        loop.call_later(args.duration, stop.set)
    await run([BinanceProvider(tuple(args.symbols.split(',')), args.backfill_days)], stop)


def main() -> None:
    parser = argparse.ArgumentParser(description='Independent public market-data worker (no trading)')
    parser.add_argument('--symbols', default='BTCUSDT,ETHUSDT')
    parser.add_argument('--backfill-days', type=int, default=365)
    parser.add_argument('--duration', type=int, default=0, help='Stop after N seconds; 0 runs continuously')
    args = parser.parse_args()
    if args.duration < 0:
        parser.error('--duration must be nonnegative')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    db.init()
    asyncio.run(main_async(args))


if __name__ == '__main__':
    main()
