"""Real upstream feeds, idempotent upserts, partial failures and background jobs."""
import argparse
import json
import math
import re
import threading
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import db

HEADERS={'User-Agent':'Mozilla/5.0 (compatible; ExplainableMarket/1.0)', 'Accept':'application/json, application/xml, text/xml'}
POOL=ThreadPoolExecutor(max_workers=3)
LOCK=threading.Lock()
ACTIVE=set()

def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=18) as r:
        return r.read(3_000_000)

def yahoo_prices(ticker):
    url=f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=6mo&interval=1d'
    data=json.loads(fetch(url))['chart']['result'][0]
    quote=data['indicators']['quote'][0]
    zone=data['meta'].get('exchangeTimezoneName','America/New_York')
    from zoneinfo import ZoneInfo
    today=datetime.now(ZoneInfo(zone)).date().isoformat()
    rows=[]
    for i, stamp in enumerate(data.get('timestamp',[])):
        close=quote['close'][i]
        if close is not None and math.isfinite(close) and close>0:
            day=datetime.fromtimestamp(stamp,ZoneInfo(zone)).date().isoformat()
            if day>=today:
                continue  # A daily candle can still be intraday. Keep completed prior days.
            rows.append((ticker,day,float(close),float(quote['volume'][i] or 0)))
    return rows, data['meta'].get('currency','USD'),'Yahoo Finance',f'https://finance.yahoo.com/quote/{ticker}/history/'

def nasdaq_prices(ticker):
    asset='etf' if ticker=='SPY' else 'stocks'
    since=(datetime.now(timezone.utc)-timedelta(days=183)).date().isoformat()
    url=f'https://api.nasdaq.com/api/quote/{ticker}/historical?assetclass={asset}&fromdate={since}&limit=140'
    data=json.loads(fetch(url))
    table=(data.get('data') or {}).get('tradesTable') or {}
    rows=[]
    for item in table.get('rows') or []:
        raw=re.sub(r'[^0-9.]','',item.get('close',''))
        if raw and float(raw)>0:
            day=datetime.strptime(item['date'],'%m/%d/%Y').date().isoformat()
            volume=re.sub(r'[^0-9.]','',item.get('volume','')) or '0'
            rows.append((ticker,day,float(raw),float(volume)))
    return sorted(rows,key=lambda r:r[1]),'USD','Nasdaq',f'https://www.nasdaq.com/market-activity/{asset}/{ticker.lower()}/historical'

def get_prices(ticker):
    for provider in (yahoo_prices,nasdaq_prices):
        try:
            result=provider(ticker)
            if len(result[0])>=2:
                return result
        except (OSError,ValueError,KeyError,TypeError,IndexError):
            continue
    raise ValueError('No se pudo consultar la fuente de precios. Reintenta más tarde; no se han generado cotizaciones.')

def get_news(ticker):
    root=ET.fromstring(fetch(f'https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US'))
    items=[]
    for item in root.findall('./channel/item')[:18]:
        headline=item.findtext('title','').strip()
        url=item.findtext('link','').strip()
        parsed=urllib.parse.urlparse(url)
        if not headline or parsed.scheme!='https' or not parsed.hostname:
            continue
        try:
            published=parsedate_to_datetime(item.findtext('pubDate')).astimezone(timezone.utc).isoformat(timespec='seconds')
        except (ValueError,TypeError,AttributeError):
            continue
        source=item.findtext('source') or parsed.hostname
        items.append((ticker,headline[:500],source[:150],url,published))
    return items

def refresh(ticker):
    db.x('UPDATE symbols SET last_attempt=? WHERE ticker=?',(now(),ticker))
    try:
        try:
            rows,currency,source,url=get_prices(ticker)
            with db.connect() as c:
                previous=c.execute('SELECT source FROM symbols WHERE ticker=?',(ticker,)).fetchone()
                if previous and previous['source'] and previous['source']!=source:
                    c.execute('DELETE FROM prices WHERE ticker=?',(ticker,))
                c.executemany('INSERT INTO prices VALUES (?,?,?,?) ON CONFLICT(ticker,date) DO UPDATE SET close=excluded.close,volume=excluded.volume',rows)
                c.execute('UPDATE symbols SET currency=?,source=?,source_url=?,fetched_at=?,price_error=NULL WHERE ticker=?',
                          (currency,source,url,now(),ticker))
        except (OSError,ValueError,KeyError,TypeError) as exc:
            db.x('UPDATE symbols SET price_error=? WHERE ticker=?',('El proveedor de precios no está disponible. Conservamos el último dato verificado.',ticker))
        try:
            items=get_news(ticker)
            with db.connect() as c:
                c.executemany('INSERT OR IGNORE INTO news(ticker,headline,source,url,published) VALUES (?,?,?,?,?)',items)
                c.execute('UPDATE symbols SET news_error=NULL WHERE ticker=?',(ticker,))
        except (OSError,ValueError,ET.ParseError):
            db.x('UPDATE symbols SET news_error=? WHERE ticker=?',('No se pudo actualizar el feed de noticias.',ticker))
    finally:
        with LOCK:
            ACTIVE.discard(ticker)

def start(tickers, force=False):
    started=[]
    for ticker in tickers[:12]:
        sym=db.q1('SELECT * FROM symbols WHERE ticker=?',(ticker,))
        if not sym:
            continue
        if sym['last_attempt']:
            elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(sym['last_attempt'])).total_seconds()
            if elapsed < (90 if force else 900):
                continue
        with LOCK:
            if ticker in ACTIVE:
                continue
            ACTIVE.add(ticker)
        POOL.submit(refresh,ticker)
        started.append(ticker)
    return started

def status():
    with LOCK:
        return sorted(ACTIVE)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Collect real public prices and RSS news')
    parser.add_argument('--loop',action='store_true')
    parser.add_argument('--interval',type=int,default=900)
    args=parser.parse_args()
    db.init()
    while True:
        list(POOL.map(refresh,[s['ticker'] for s in db.q('SELECT ticker FROM symbols')]))
        print('Collection complete:',now(),flush=True)
        if not args.loop: break
        time.sleep(max(90,args.interval))
