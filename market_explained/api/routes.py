"""Bounded read APIs with explicit errors, source attribution and no upstream calls."""
import hashlib
import json
from datetime import datetime
from flask import Blueprint, jsonify, render_template, request

import charts
import db
from market_explained.markets.events import utcnow, timestamp
from market_explained.providers.base import CAPABILITIES
from market_explained.storage import repository
from market_explained.security.display import restricted
from market_explained.intelligence.data import latest

api = Blueprint('market_api', __name__, url_prefix='/api/v1')
pages = Blueprint('markets', __name__)
CLASSES = {'stocks':'Acciones', 'forex':'Divisas', 'crypto':'Criptomonedas', 'indices':'Índices', 'commodities':'Materias primas'}
STATUS_LABELS = {'LIVE':'En vivo','DELAYED':'Con retraso','HISTORICAL':'Histórico','STALE':'Desactualizado','DEMO':'Demostración','UNAVAILABLE':'No disponible'}


class APIError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code, self.message, self.status = code, message, status


@api.errorhandler(APIError)
def api_error(error):
    return jsonify(error={'code':error.code,'message':error.message}), error.status


@api.before_request
def limit_reads():
    ip = hashlib.sha256((request.remote_addr or 'unknown').encode()).hexdigest()[:24]
    if not db.allow('v1:' + ip, 120, 60):
        response = jsonify(error={'code':'rate_limited','message':'Espera un minuto antes de consultar de nuevo.'})
        response.status_code = 429
        response.headers['Retry-After'] = '60'
        return response


def pagination() -> tuple[int,int]:
    try:
        limit = int(request.args.get('limit','100'))
        offset = int(request.args.get('offset','0'))
    except ValueError:
        raise APIError('invalid_pagination','limit y offset deben ser enteros.') from None
    if not 1 <= limit <= 200 or not 0 <= offset <= 1_000_000:
        raise APIError('invalid_pagination','limit: 1–200; offset: 0–1000000.')
    return limit, offset


def instrument(symbol: str) -> dict:
    row = db.q1('SELECT * FROM instruments WHERE symbol=? OR instrument_id=?', (symbol.upper(),symbol))
    if not row:
        raise APIError('unknown_instrument','Instrumento no registrado.',404)
    return row


def catalog() -> list[dict]:
    asset_class = request.args.get('asset_class','')
    query = request.args.get('q','').strip()
    if asset_class and asset_class not in CLASSES:
        raise APIError('invalid_asset_class','Clase de activo desconocida.')
    if len(query) > 80:
        raise APIError('invalid_query','La búsqueda admite hasta 80 caracteres.')
    sql = 'SELECT * FROM instruments WHERE 1=1'
    params = []
    if asset_class:
        sql += ' AND asset_class=?'
        params.append(asset_class)
    if query:
        sql += ' AND (instr(lower(symbol),lower(?))>0 OR instr(lower(name),lower(?))>0)'
        params += [query,query]
    return db.q(sql + ' ORDER BY asset_class,symbol',params)


def provider_status() -> list[dict]:
    result = []
    for capability in CAPABILITIES:
        row = db.q1('SELECT * FROM provider_health WHERE provider=?', (capability['provider'],))
        if row and (utcnow()-datetime.fromisoformat(row['updated_at'])).total_seconds()>(1800 if capability['provider']=='twelve_data' else repository.FRESH_SECONDS):
            row['connection'] = 'STALE'
        if row is None and capability['provider'] in ('yahoo','nasdaq'):
            source = 'Yahoo Finance' if capability['provider']=='yahoo' else 'Nasdaq'
            daily = db.q1('SELECT max(fetched_at) fetched_at FROM symbols WHERE source=?', (source,))
            row = {'connection':'HISTORICAL' if daily and daily['fetched_at'] else 'UNAVAILABLE',
                   'last_event_at':daily['fetched_at'] if daily else None}
        if row and capability['provider']=='twelve_data':
            row['instruments'] = db.q('SELECT i.symbol,s.state,s.error_code,s.checked_at,s.next_attempt_at FROM provider_instrument_status s JOIN instruments i USING(instrument_id) WHERE s.provider=?',('twelve_data',))
        result.append({**capability,'health':row or {'connection':'UNAVAILABLE' if capability['implemented'] else 'NOT_IMPLEMENTED'}})
    return result


@api.get('/markets')
def markets_api():
    return jsonify(data=[{'asset_class':key,'name':value,'instrument_count':db.q1(
        'SELECT count(*) n FROM instruments WHERE asset_class=?',(key,))['n'],
        'implemented':True} for key,value in CLASSES.items()])


@api.get('/instruments')
def instruments_api():
    limit, offset = pagination()
    rows = catalog()
    return jsonify(data=rows[offset:offset+limit],pagination={'limit':limit,'offset':offset,'total':len(rows)})


@api.get('/market/<symbol>')
def market_api(symbol):
    return jsonify(data=repository.snapshot(instrument(symbol)['instrument_id']),asof=timestamp(utcnow()))


@api.get('/market/<symbol>/history')
def history_api(symbol):
    item = instrument(symbol)
    limit, offset = pagination()
    if restricted(item['instrument_id']):
        raise APIError('display_restricted','La visualización externa de Twelve Data no está autorizada.',403)
    source = request.args.get('provider')
    if source and len(source)>80:
        raise APIError('invalid_provider','Proveedor inválido.')
    if item['asset_class']=='stocks':
        params = (item['symbol'],source,source)
        total = db.q1('SELECT count(*) n FROM stock_observations WHERE ticker=? AND (? IS NULL OR provider=?)', params)['n']
        rows = db.q('''SELECT * FROM stock_observations WHERE ticker=? AND (? IS NULL OR provider=?)
            ORDER BY date DESC,provider,received_at DESC LIMIT ? OFFSET ?''',(*params,limit,offset))
    else:
        rows = repository.history(item['instrument_id'],limit,offset,source)
        total = db.q1('SELECT count(*) n FROM market_events WHERE instrument_id=? AND (? IS NULL OR provider=?)',
            (item['instrument_id'],source,source))['n']
    return jsonify(data=rows,pagination={'limit':limit,'offset':offset,'total':total})


@api.get('/providers/status')
def providers_api():
    return jsonify(data=provider_status())


@api.get('/system/health')
def system_api():
    db.q1('SELECT 1')
    return jsonify(status='ok',database='connected',worker_independent=True,
        schema_versions=[r['version'] for r in db.q('SELECT version FROM schema_migrations')],providers=provider_status(),
        forecasting=db.q1("SELECT * FROM provider_health WHERE provider='forecasting'"))


def prediction_for(symbol):
    item = instrument(symbol)
    if restricted(item['instrument_id']):
        raise APIError('display_restricted','La visualización externa de Twelve Data no está autorizada.',403)
    prediction = latest(item['instrument_id'])
    if not prediction:
        raise APIError('prediction_unavailable','Aún no hay un pronóstico: se requieren al menos 120 cierres y el proceso de entrenamiento.',503)
    # Model artifacts stay in the private model registry, not in public responses.
    prediction['model_metadata']['explanation'].pop('booster_json',None)
    return prediction


@api.get('/predictions/<symbol>')
def predictions_api(symbol):
    return jsonify(data=prediction_for(symbol))


@api.get('/analysis/<symbol>')
def analysis_api(symbol):
    result = prediction_for(symbol)
    return jsonify(data=dict(instrument=result['instrument'],provider=result['provider'],
        data_cutoff=result['data_cutoff_timestamp'],indicators=result['indicators'],
        explanation=result['model_metadata']['explanation'],
        features=result['model_metadata']['features'],data_quality=result['data_quality']))


@pages.get('/intelligence')
def intelligence():
    selected = request.args.get('symbol','BTCUSDT')
    item = instrument(selected)
    result = None if restricted(item['instrument_id']) else latest(item['instrument_id'])
    return render_template('intelligence.html',instruments=catalog(),selected=item,
        prediction=result,restricted=restricted(item['instrument_id']))


@pages.errorhandler(APIError)
def page_error(error):
    return render_template('error.html',code=error.status,message=error.message), error.status


@pages.get('/markets')
def explorer():
    cards = [repository.snapshot(row['instrument_id']) for row in catalog()]
    return render_template('markets.html',cards=cards,classes=CLASSES,status_labels=STATUS_LABELS,
        selected_class=request.args.get('asset_class',''),query=request.args.get('q',''))


@pages.get('/market/<symbol>')
def detail(symbol):
    item = instrument(symbol)
    if item['asset_class']=='stocks':
        from flask import redirect, url_for
        return redirect(url_for('symbol_detail',ticker=item['symbol']))
    view = repository.snapshot(item['instrument_id'])
    provider = 'twelve_data' if item['instrument_id'].startswith('twelve:') else 'binance'
    rows = [] if restricted(item['instrument_id']) else db.q('''SELECT payload FROM market_events WHERE instrument_id=? AND provider=?
        AND event_type='candle' AND json_extract(payload,'$.interval')='1d'
        AND json_extract(payload,'$.candle_closed')=1 ORDER BY event_time,received_at''',(item['instrument_id'],provider))
    # Retain revisions in history, but display the latest observation for each day.
    by_day = {json.loads(r['payload'])['candle_open_time'][:10]:json.loads(r['payload']) for r in rows}
    candles = list(by_day.values())[-365:]
    chart = charts.price_chart([r['candle_open_time'][:10] for r in candles],
        [float(r['price']) for r in candles],label='Daily closes · ' + provider + ' · ' + item['quote_currency'] + ' · UTC') if candles else None
    return render_template('market.html',view=view,chart=chart,status_labels=STATUS_LABELS)


@pages.get('/sources')
def sources():
    return render_template('sources.html',providers=provider_status())
