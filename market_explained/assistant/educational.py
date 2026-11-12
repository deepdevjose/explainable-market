"""Bounded, deterministic explanations. Never presented as model output."""
TEXT = {
    'es': {
        'prefix': 'Guía educativa local · sin IA generativa. ',
        'volatility': 'La volatilidad describe cuánto fluctúa un precio, no hacia dónde irá. Una volatilidad mayor indica oscilaciones mayores; no garantiza rentabilidad.',
        'correlation': 'Dos hechos pueden coincidir sin que uno cause el otro. Las noticias y los precios permiten explorar coincidencias temporales, no demostrar causas.',
        'sentiment': 'El sentimiento clasifica el tono de un titular, no predice precios. El análisis de titulares con el proveedor de IA requiere configuración y saldo del proveedor.',
        'diversification': 'Diversificar distribuye exposición entre activos o factores. Ayuda a entender concentraciones de riesgo, pero no elimina las pérdidas.',
        'screen': 'Acciones: cierres diarios históricos. Cripto: Binance Spot en USDT. Revisa fuente, fecha y estado; solo «En vivo» indica un evento reciente con colector conectado. USDT no es USD.',
        'unknown': 'Puedo explicar esta pantalla, volatilidad, correlación, sentimiento o diversificación mediante textos educativos revisados. Para conversación libre hace falta configurar el proveedor de IA. No doy recomendaciones de inversión.',
    },
    'en': {
        'prefix': 'Local educational guide · no generative AI. ',
        'volatility': 'Volatility describes how much a price fluctuates, not its future direction. Higher volatility means larger swings; it does not guarantee returns.',
        'correlation': 'Events may coincide without one causing the other. News and prices can reveal temporal associations, not establish causes.',
        'sentiment': 'Sentiment classifies headline tone; it does not predict prices. AI headline analysis requires provider configuration and credit.',
        'diversification': 'Diversification spreads exposure across assets or factors. It helps understand concentrated risk but does not eliminate losses.',
        'screen': 'Stocks show historical daily closes. Crypto uses Binance Spot in USDT. Check source, timestamp and status; only Live means a recent event with a connected collector. USDT is not USD.',
        'unknown': 'I can explain this screen, volatility, correlation, sentiment or diversification using reviewed educational text. Open conversation requires AI provider configuration. I do not provide investment recommendations.',
    },
    'zh-Hans': {
        'prefix': '本地教育指南 · 不使用生成式 AI。',
        'volatility': '波动率描述价格起伏的程度，而不是未来方向。波动率越高通常意味着起伏越大，并不保证收益。',
        'correlation': '事件可能同时发生，但并不表示互为因果。新闻与价格可以显示时间关联，不能证明原因。',
        'sentiment': '情绪分析对标题语气进行分类，不能预测价格。AI 新闻分析需要配置提供方并具备可用余额。',
        'diversification': '分散化将风险敞口分布于不同资产或因素，帮助理解集中风险，但不能消除损失。',
        'screen': '股票显示历史每日收盘价。加密资产使用 Binance 现货 USDT 报价。请核对来源、时间及状态；仅实时状态表示采集器已连接且事件近期收到。USDT 不等于美元。',
        'unknown': '我可以使用已审核教育文本解释当前页面、波动率、相关性、情绪或分散化。开放对话需要配置 AI 提供方。我不提供投资建议。',
    },
}


def explain(question, context):
    language = context.get('response_language', 'es')
    texts = TEXT.get(language, TEXT['es'])
    question = question.casefold()
    topic = 'unknown'
    for key, words in (
        ('volatility', ('volatil', '波动')),
        ('correlation', ('correla', 'causal', '相关', '因果')),
        ('sentiment', ('sentim', '情绪')),
        ('diversification', ('diversif', '分散')),
        ('screen', ('pantalla', 'screen', '页面', '界面', '市场', 'datos', 'data')),
    ):
        if any(word in question for word in words):
            topic = key
            break
    return texts['prefix'] + texts[topic]
