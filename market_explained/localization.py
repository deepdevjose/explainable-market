"""Explicit UI catalogs; provider headlines and user content remain verbatim."""
import json
from pathlib import Path
from flask import g, has_request_context, request, session

LANGUAGES = {'es': 'Español', 'en': 'English', 'zh-Hans': '简体中文'}
MESSAGES = json.loads((Path(__file__).parent / 'locales/messages.json').read_text())


def translate(message):
    if not isinstance(message, str):
        return message
    language = getattr(g, 'language', 'es') if has_request_context() else 'es'
    return MESSAGES.get(message, {}).get(language, message)


def install(app):
    app.jinja_env.filters['marketprice'] = format_price

    @app.before_request
    def choose_language():
        selected = request.args.get('lang')
        if selected in LANGUAGES:
            session['language'] = selected
        g.language = session.get('language', 'es')
        if g.language not in LANGUAGES:
            g.language = 'es'

    @app.context_processor
    def language_context():
        return {'_': translate, 'language': g.language, 'languages': LANGUAGES}

    @app.after_request
    def language_header(response):
        response.headers['Content-Language'] = g.language
        if response.is_json and g.language != 'es':
            body = response.get_json(silent=True)
            if isinstance(body, dict):
                for key in ('error', 'message'):
                    if isinstance(body.get(key), str):
                        body[key] = translate(body[key])
                    elif key == 'error' and isinstance(body.get(key), dict):
                        body[key]['message'] = translate(body[key].get('message', ''))
                response.set_data(app.json.dumps(body))
        return response

    @app.get('/api/v1/translations')
    def translation_catalog():
        return {key: value.get(g.language, key) for key, value in MESSAGES.items()}


def format_price(value):
    """Format decimal strings for display without float conversion."""
    if value is None or value == '—':
        return '—'
    raw = str(value)
    whole, _, fraction = raw.partition('.')
    if not whole.lstrip('-').isdigit() or (fraction and not fraction.isdigit()):
        return raw
    fraction = fraction.rstrip('0').ljust(2, '0')
    import re
    language = getattr(g, 'language', 'es') if has_request_context() else 'es'
    group, decimal = ('.', ',') if language == 'es' else (',', '.')
    whole = re.sub(r'(\d)(?=(\d{3})+$)', r'\1' + group, whole)
    return whole + decimal + fraction
