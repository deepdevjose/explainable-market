"""Explainable Market: real-source research and educational assistance."""
import csv
import hashlib
import io
import os
import re
import secrets
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import urlsplit

from flask import Flask, Response, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import ai
import charts
import collector
import config
import db

app=Flask(__name__, template_folder=str(config.ROOT / 'templates'),
          static_folder=str(config.ROOT / 'static'))
app.config.update(SECRET_KEY=config.SECRET_KEY, MAX_CONTENT_LENGTH=16*1024,
    SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=config.PRODUCTION or os.environ.get('COOKIE_SECURE','0')=='1',
    PERMANENT_SESSION_LIFETIME=timedelta(days=7))
from market_explained.localization import install as install_localization
install_localization(app)
db.init()
from market_explained.api.routes import api as market_api, pages as market_pages
app.register_blueprint(market_api)
app.register_blueprint(market_pages)
LABELS={1:'Positivo',0:'Neutral',-1:'Negativo',None:'Sin analizar'}
PAGES={'landing':'Inicio de Explainable Market: plataforma para relacionar precios con noticias y aprender.',
       'dashboard':'Panorama del mercado. Cierres diarios, variación respecto al cierre anterior y noticias relacionadas.',
       'watchlist':'Seguimiento personal. Añadir o quitar activos de la lista guardada.',
       'news_page':'Noticias de fuentes externas. El sentimiento es una clasificación de un titular, no una señal de inversión.',
       'learn':'Biblioteca educativa y metodología: correlación no significa causalidad.',
       'symbol_detail':'Detalle de activo. Serie de cierres y coincidencias temporales de noticias; ventanas completas de 1, 3 y 7 sesiones.',
       'markets.explorer':'Explorador de acciones históricas y criptomonedas de Binance Spot con estados de frescura y proveedor.',
       'markets.detail':'Detalle de instrumento con atribución. Binance usa USDT; Twelve Data usa consultas cada 15 minutos. Las velas diarias son históricas.',
       'markets.intelligence':'Pronósticos educativos de retornos con persistencia, ridge y XGBoost. Se seleccionan por calibración y se evalúan después cronológicamente. No son recomendaciones ni resultados garantizados.',
       'markets.sources':'Disponibilidad de proveedores, atribución, límites y condiciones de uso de datos. Integración planificada no implica datos disponibles.',
       'login':'Iniciar sesión para guardar una lista personal.', 'register':'Crear una cuenta propia.'}


def owner():
    return 'user:'+str(session['user_id']) if session.get('user_id') else 'guest:'+session['visitor']

def csrf_token():
    if 'csrf' not in session: session['csrf']=secrets.token_urlsafe(32)
    return session['csrf']

@app.before_request
def protect():
    if request.endpoint=='static': return
    session.setdefault('visitor',secrets.token_urlsafe(20))
    if request.method in ('POST','PUT','DELETE','PATCH'):
        supplied=request.headers.get('X-CSRF-Token') or request.form.get('csrf_token','')
        if not supplied or not secrets.compare_digest(supplied,session.get('csrf','')):
            return jsonify(error='La sesión cambió. Recarga la página e inténtalo de nuevo.'),403
        origin=request.headers.get('Origin')
        if origin and urlsplit(origin).netloc!=request.host:
            return jsonify(error='Origen no permitido.'),403

@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    response.headers['Cache-Control']='no-store'
    return response

@app.context_processor
def context():
    return dict(csrf_token=csrf_token,sentiment_label=LABELS,chat_ready=bool(config.DEEPSEEK_KEY),
                active_jobs=collector.status(),
                page=request.endpoint or '',active_ticker=request.view_args.get('ticker','') if request.view_args else '',
                user=db.q1('SELECT name,email FROM users WHERE id=?',(session['user_id'],)) if session.get('user_id') else None)

@app.template_filter('pct')
def pct(v): return '—' if v is None else f'{v:+.2f}%'

@app.template_filter('money')
def money(v): return '—' if v is None else f'{v:,.2f}'

@app.template_filter('shortdate')
def shortdate(v): return str(v).replace('T',' · ')[:18] if v else 'Pendiente'

def login_required(fn):
    @wraps(fn)
    def wrapped(*args,**kwargs):
        if not session.get('user_id'):
            flash('Inicia sesión para guardar tu seguimiento.','info')
            return redirect(url_for('login',next=request.path))
        return fn(*args,**kwargs)
    return wrapped

def limited(name,count,seconds):
    ip=hashlib.sha256((request.remote_addr or 'unknown').encode()).hexdigest()[:24]
    return db.allow(name+':'+ip,count,seconds)

def json_body():
    body=request.get_json(silent=True)
    if not isinstance(body,dict): abort(400)
    return body

def safe_next():
    target=request.args.get('next','')
    return target if target.startswith('/') and not target.startswith('//') and '\\' not in target else url_for('dashboard')

@app.route('/register',methods=['GET','POST'])
def register():
    error=None
    if request.method=='POST':
        if not limited('register',10,3600): abort(429)
        name=request.form.get('name','').strip()
        email=request.form.get('email','').strip().lower()
        password=request.form.get('password','')
        if not 2<=len(name)<=60 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email) or len(email)>254:
            error='Escribe tu nombre y un correo válido.'
        elif not 10<=len(password)<=200:
            error='Usa una contraseña de entre 10 y 200 caracteres.'
        else:
            try:
                uid=db.x('INSERT INTO users(email,password_hash,name,created_at) VALUES (?,?,?,?)',
                    (email,generate_password_hash(password),name,collector.now()))
                session.clear();session.update(user_id=uid,visitor=secrets.token_urlsafe(20),permanent=True)
                return redirect(url_for('watchlist'))
            except sqlite3.IntegrityError:
                error='No se pudo crear la cuenta con ese correo. Prueba iniciar sesión.'
    return render_template('login.html',register=True,error=error)

@app.route('/login',methods=['GET','POST'])
def login():
    error=None
    if request.method=='POST':
        if not limited('login',20,900): abort(429)
        email=request.form.get('email','').strip().lower()
        password=request.form.get('password','')
        user=db.q1('SELECT * FROM users WHERE email=?',(email,))
        if user and len(password)<=200 and check_password_hash(user['password_hash'],password):
            session.clear();session.update(user_id=user['id'],visitor=secrets.token_urlsafe(20),permanent=True)
            return redirect(safe_next())
        error='El correo o la contraseña no son correctos.'
    return render_template('login.html',register=False,error=error)

@app.post('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

def price_rows(ticker):
    return db.q('SELECT date,close,volume FROM prices WHERE ticker=? ORDER BY date',(ticker,))

def asset(ticker):
    sym=db.q1('SELECT * FROM symbols WHERE ticker=?',(ticker,))
    if not sym: return None
    rows=price_rows(ticker)
    sym.update(close=rows[-1]['close'] if rows else None,asof=rows[-1]['date'] if rows else None,
        change=(rows[-1]['close']/rows[-2]['close']-1)*100 if len(rows)>1 else None,
        sparkline=charts.sparkline([r['close'] for r in rows[-30:]]))
    return sym

def news_for(ticker=None,sentiment=None,limit=30):
    sql='SELECT n.*,s.name FROM news n JOIN symbols s ON s.ticker=n.ticker WHERE 1=1'
    params=[]
    if ticker: sql+=' AND n.ticker=?';params.append(ticker)
    if sentiment in (-1,0,1): sql+=' AND n.sentiment=?';params.append(sentiment)
    sql+=' ORDER BY n.published DESC,n.id DESC LIMIT ?';params.append(limit)
    return db.q(sql,params)

def impact(rows, published):
    # Regular US close only; shortened sessions require a licensed market calendar.
    from zoneinfo import ZoneInfo
    local=datetime.fromisoformat(published).astimezone(ZoneInfo('America/New_York'))
    day=local.date().isoformat()
    after_close=local.hour>=16
    idx=next((i for i,r in enumerate(rows) if r['date']>day or (r['date']==day and not after_close)),None)
    if idx is None or idx==0: return [None,None,None],None
    base=rows[idx-1]['close']
    values=[(rows[idx+n-1]['close']/base-1)*100 if idx+n-1<len(rows) else None for n in (1,3,7)]
    return values,rows[idx]['date']

@app.get('/')
def landing():
    return render_template('landing.html',featured=asset('AAPL'))

@app.get('/app')
def dashboard():
    tickers=[r['ticker'] for r in db.q('SELECT ticker FROM watchlist WHERE user_id=? ORDER BY added_at',(session.get('user_id',-1),))]
    personal=bool(tickers)
    if not tickers: tickers=['SPY','AAPL','MSFT','NVDA']
    if not app.testing: collector.start(tickers)
    cards=[asset(t) for t in tickers]
    selected=request.args.get('ticker','').upper()
    if selected not in tickers: selected=tickers[0]
    focus=asset(selected);rows=price_rows(selected)
    recent=news_for(selected,limit=5)
    dates=[r['date'] for r in rows]
    markers=[]
    for n in recent:
        _,eventday=impact(rows,n['published'])
        if eventday in dates: markers.append((dates.index(eventday),n['sentiment'],n['headline'],False))
    chart=charts.price_chart(dates,[r['close'] for r in rows],markers) if rows else None
    return render_template('dashboard.html',cards=cards,focus=focus,chart=chart,recent_news=recent,
                           personal=personal,active_jobs=collector.status())

@app.route('/watchlist',methods=['GET','POST'])
@login_required
def watchlist():
    uid=session['user_id']
    if request.method=='POST':
        ticker=request.form.get('ticker','').upper()
        if not db.q1('SELECT ticker FROM symbols WHERE ticker=?',(ticker,)): abort(400)
        action=request.form.get('action')
        if action=='add':
            db.x('INSERT OR IGNORE INTO watchlist VALUES (?,?,?)',(uid,ticker,collector.now()))
            if not app.testing: collector.start([ticker])
            flash(ticker+' añadido a tu seguimiento.','success')
        elif action=='remove':
            db.x('DELETE FROM watchlist WHERE user_id=? AND ticker=?',(uid,ticker))
            flash(ticker+' eliminado del seguimiento.','info')
        else: abort(400)
        return redirect(url_for('watchlist'))
    saved={r['ticker'] for r in db.q('SELECT ticker FROM watchlist WHERE user_id=?',(uid,))}
    return render_template('watchlist.html',symbols=db.q('SELECT * FROM symbols ORDER BY ticker'),saved=saved)

@app.get('/symbol/<ticker>')
def symbol_detail(ticker):
    ticker=ticker.upper();sym=asset(ticker)
    if not sym: abort(404)
    if not app.testing: collector.start([ticker])
    days={'1m':22,'3m':66,'6m':140}
    period=request.args.get('period','6m')
    if period not in days: period='6m'
    allrows=price_rows(ticker);rows=allrows[-days[period]:]
    dates=[r['date'] for r in rows];closes=[r['close'] for r in rows]
    impacts=[];markers=[]
    for n in news_for(ticker,limit=30):
        values,eventday=impact(allrows,n['published'])
        impacts.append({'news':n,'values':values,'eventday':eventday})
        if eventday in dates: markers.append((dates.index(eventday),n['sentiment'],n['headline'],False))
    return render_template('symbol.html',sym=sym,chart=charts.price_chart(dates,closes,markers) if rows else None,
        impacts=impacts,period=period,high=max(closes) if closes else None,low=min(closes) if closes else None,
        period_change=(closes[-1]/closes[0]-1)*100 if len(closes)>1 else None,
        saved=bool(db.q1('SELECT 1 FROM watchlist WHERE user_id=? AND ticker=?',(session.get('user_id',-1),ticker))))

@app.get('/news')
def news_page():
    ticker=request.args.get('ticker','').upper()
    sentiment=request.args.get('sentiment',type=int)
    return render_template('news.html',items=news_for(ticker or None,sentiment,60),symbols=db.q('SELECT * FROM symbols ORDER BY ticker'),
                           sel_ticker=ticker,sel_sentiment=sentiment)

@app.get('/learn')
def learn(): return render_template('learn.html')

@app.post('/api/refresh')
def refresh_api():
    if not limited('refresh',30,3600): return jsonify(error='Espera unos minutos antes de volver a actualizar.'),429
    payload=json_body()
    ticker=payload.get('ticker','')
    if not isinstance(ticker,str): abort(400)
    tickers=[ticker.upper()] if ticker else ['SPY','AAPL','MSFT','NVDA']
    if session.get('user_id') and not ticker:
        saved=[r['ticker'] for r in db.q('SELECT ticker FROM watchlist WHERE user_id=?',(session['user_id'],))]
        if saved: tickers=saved
    if any(not db.q1('SELECT 1 FROM symbols WHERE ticker=?',(t,)) for t in tickers): abort(400)
    started=collector.start(tickers,force=True)
    return jsonify(started=started,active=collector.status(),message='Actualización solicitada.' if started else 'Los datos se actualizaron recientemente o ya se están consultando.'),202

@app.get('/api/status')
def status_api():
    return jsonify(active=collector.status())

@app.post('/api/analyze/<ticker>')
@login_required
def analyze_api(ticker):
    ticker=ticker.upper()
    if not db.q1('SELECT 1 FROM symbols WHERE ticker=?',(ticker,)): abort(404)
    if not limited('analyze',6,3600) or not db.allow('ai-global',200,86400):
        return jsonify(error='Se alcanzó el límite de análisis. Inténtalo más tarde.'),429
    items=db.q('SELECT id,headline FROM news WHERE ticker=? AND sentiment IS NULL ORDER BY published DESC LIMIT 8',(ticker,))
    try:
        results=ai.analyze_news(items)
        with db.connect() as c:
            for r in results:
                c.execute('UPDATE news SET sentiment=?,rationale=?,analyzed_at=? WHERE id=?',
                    (r['sentiment'],r['rationale'],collector.now(),r['id']))
        return jsonify(analyzed=len(results),message=f'{len(results)} titulares analizados.')
    except ai.AIError as exc: return jsonify(error=str(exc)),503

@app.route('/api/chat',methods=['GET','POST','DELETE'])
def chat_api():
    who=owner()
    if request.method=='GET':
        return jsonify(messages=db.q('SELECT role,content FROM (SELECT id,role,content FROM messages WHERE owner=? ORDER BY id DESC LIMIT 30) ORDER BY id',(who,)))
    if request.method=='DELETE':
        db.x('DELETE FROM messages WHERE owner=?',(who,))
        return jsonify(ok=True)
    payload=json_body()
    question=payload.get('message','')
    if not isinstance(question,str) or not 1<=len(question.strip())<=1200:
        return jsonify(error='Escribe una pregunta de entre 1 y 1.200 caracteres.'),400
    if not limited('chat',30,3600) or not db.allow('ai-global',200,86400):
        return jsonify(error='Llegaste al límite de consultas. Inténtalo más tarde.'),429
    page=payload.get('page','dashboard')
    if not isinstance(page,str): page='dashboard'
    ticker=payload.get('ticker','')
    ticker=ticker.upper() if isinstance(ticker,str) else ''
    sym=asset(ticker) if ticker else None
    if sym: sym={k:sym[k] for k in ('ticker','name','close','change','asof','source','fetched_at','price_error')}
    elif ticker:
        instrument=db.q1('SELECT * FROM instruments WHERE symbol=?',(ticker,))
        if instrument:
            from market_explained.storage.repository import snapshot
            view=snapshot(instrument['instrument_id'])
            observation=view['observation'] or {}
            sym={'ticker':ticker,'name':instrument['name'],'currency':instrument['quote_currency'],
                 'price':observation.get('price'),'source':observation.get('provider'),
                 'asof':observation.get('event_time'),'received_at':observation.get('received_at'),
                 'status':view['status'],'quality_flags':observation.get('quality_flags',[])}
    context={'response_language':g.language,'screen':PAGES.get(page,PAGES['dashboard']),'asset':sym,
        'news':[{k:n[k] for k in ('id','ticker','headline','published','source','url','sentiment')} for n in news_for(ticker if sym else None,limit=5)],
        'data_policy':'Acciones: cierres diarios históricos. Cripto: observaciones de Binance Spot en USDT; solo LIVE indica recepción reciente conectada. STALE es desactualizado, HISTORICAL no es en vivo y UNAVAILABLE es desconocido. Correlación no implica causalidad.'}
    history=db.q('SELECT role,content FROM (SELECT id,role,content FROM messages WHERE owner=? ORDER BY id DESC LIMIT 8) ORDER BY id',(who,))
    try:
        answer=ai.answer(question.strip(),history,context)
        with db.connect() as c:
            c.executemany('INSERT INTO messages(owner,role,content,created_at) VALUES (?,?,?,?)',
                [(who,'user',question.strip(),collector.now()),(who,'assistant',answer,collector.now())])
            c.execute('DELETE FROM messages WHERE owner=? AND id NOT IN (SELECT id FROM messages WHERE owner=? ORDER BY id DESC LIMIT 30)',(who,who))
        used=[n for n in context['news'] if f"[{n['id']}]" in answer]
        return jsonify(answer=answer,sources=used)
    except ai.AIError as exc: return jsonify(error=str(exc)),503

@app.get('/api/asset/<ticker>')
def asset_api(ticker):
    sym=asset(ticker.upper())
    if not sym: abort(404)
    sym.pop('sparkline',None)
    return jsonify(asset=sym,prices=price_rows(ticker.upper()),news=news_for(ticker.upper(),limit=15))

@app.get('/export/<ticker>.csv')
def export(ticker):
    ticker=ticker.upper()
    if not db.q1('SELECT 1 FROM symbols WHERE ticker=?',(ticker,)): abort(404)
    stream=io.StringIO();writer=csv.writer(stream)
    writer.writerow(['ticker','date','close','volume','source'])
    source=db.q1('SELECT source FROM symbols WHERE ticker=?',(ticker,))['source']
    for r in price_rows(ticker): writer.writerow([ticker,r['date'],r['close'],r['volume'],source])
    return Response(stream.getvalue(),mimetype='text/csv',headers={'Content-Disposition':f'attachment; filename={ticker}.csv'})

@app.get('/health')
def health():
    db.q1('SELECT 1 AS ok')
    return jsonify(status='ok',database='connected',ai_configured=bool(config.DEEPSEEK_KEY))

@app.errorhandler(404)
@app.errorhandler(400)
@app.errorhandler(429)
@app.errorhandler(413)
def error_page(error):
    messages={400:'La solicitud no es válida.',404:'Esta página no existe.',429:'Demasiadas solicitudes. Espera unos minutos.',413:'La solicitud es demasiado grande.'}
    text=messages.get(error.code,'No se pudo completar la solicitud.')
    if request.path.startswith('/api/v1/'):
        return jsonify(error={'code':'http_'+str(error.code),'message':text}),error.code
    if request.path.startswith('/api/'): return jsonify(error=text),error.code
    return render_template('error.html',code=error.code,message=text),error.code

def serve():
    """Local Waitress entry point; trust forwarded headers only from an exact proxy."""
    import logging
    from waitress import serve as waitress_serve
    proxy = os.environ.get('TRUSTED_PROXY', '')
    if proxy == '*':
        raise RuntimeError('TRUSTED_PROXY must identify an exact trusted proxy IP.')
    if config.EPHEMERAL_SECRET:
        logging.warning('Development session key is ephemeral. Export SECRET_KEY for persistent sessions.')
    options = {}
    if proxy:
        options.update(trusted_proxy=proxy, trusted_proxy_count=1,
                       trusted_proxy_headers={'x-forwarded-for', 'x-forwarded-proto'})
    waitress_serve(app, host=os.environ.get('HOST','127.0.0.1'),
                   port=int(os.environ.get('PORT','5050')), threads=8, **options)
