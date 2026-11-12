"""Server-side SVG charts — no JS/CDN needed, works fully offline."""
from html import escape
from math import isfinite


def _scale(value, lo, hi, lo_px, hi_px):
    if hi == lo:
        hi = lo + 1
    return lo_px + (value - lo) / (hi - lo) * (hi_px - lo_px)


def _segments(closes, xs, ys, stroke_width=2):
    """Color each observed change, rather than the net change of the whole series."""
    parts = []
    for i in range(1, len(closes)):
        direction = 'up' if closes[i] > closes[i-1] else ('down' if closes[i] < closes[i-1] else 'flat')
        parts.append(f'<line x1="{xs[i-1]:.1f}" y1="{ys[i-1]:.1f}" x2="{xs[i]:.1f}" y2="{ys[i]:.1f}" '
                     f'class="price-segment price-{direction}" data-direction="{direction}" '
                     f'stroke-width="{stroke_width}" stroke-linecap="round"/>')
    return ''.join(parts)


def _legend(forecast=False):
    from market_explained.localization import translate
    items = [('up','↑','Sube'),('down','↓','Baja'),('flat','→','Sin cambio')]
    if forecast:
        items.append(('forecast','⇢','Predicción (estimación)'))
        items.append(('interval','▧','Intervalo empírico nominal del 80%'))
    return '<div class="chart-legend">'+''.join(
        f'<span><i class="legend-{kind}" aria-hidden="true">{symbol}</i>{escape(translate(text))}</span>'
        for kind,symbol,text in items)+'</div>'


def sparkline(closes, width=130, height=38):
    if len(closes) < 2:
        return ""
    lo, hi = min(closes), max(closes)
    xs = [ _scale(i, 0, len(closes) - 1, 1, width - 1) for i in range(len(closes)) ]
    ys = [ _scale(c, lo, hi, height - 3, 3) for c in closes ]
    return (f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'class="sparkline">{_segments(closes,xs,ys,1.6)}</svg>')


def price_chart(dates, closes, markers=None, width=920, height=360, label='Cierres diarios y noticias relacionadas', *, forecast=None):
    """Line chart with news markers.

    markers: list of (index, sentiment, headline, is_market) tuples.
    """
    from market_explained.localization import translate
    if not closes or len(dates) != len(closes):
        return ''
    label = translate(label)
    markers = markers or []
    pad_l, pad_r, pad_t, pad_b = 64, 18, 18, 30
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b
    extent = list(closes)
    if forecast:
        predicted, lower, upper = (float(forecast[k]) for k in ('predicted_value','lower_value','upper_value'))
        if not all(isfinite(v) and v > 0 for v in (predicted,lower,upper)) or not lower <= predicted <= upper:
            raise ValueError('Invalid forecast chart values')
        extent += [predicted,lower,upper]
    lo, hi = min(extent), max(extent)
    span = (hi - lo) or 1
    lo -= span * 0.06
    hi += span * 0.06
    n = len(closes)

    def X(i):
        # Reserve a separate horizon; its width does not imply a calendar duration.
        return _scale(i, 0, n - 1, pad_l, pad_l + plot_w * (0.78 if forecast else 1))

    def Y(v):
        return _scale(v, lo, hi, pad_t + plot_h, pad_t)

    area = (f"M {X(0):.1f},{pad_t + plot_h} L "
            + " L ".join(f"{X(i):.1f},{Y(c):.1f}" for i, c in enumerate(closes))
            + f" L {X(n - 1):.1f},{pad_t + plot_h} Z")

    parts = [f'<svg viewBox="0 0 {width} {height}" class="price-chart" role="img" aria-label="{escape(label, quote=True)}"><title>{escape(label)}</title>']
    if forecast:
        cutoff_x, future_x = X(n-1), pad_l + plot_w
        parts.append(f'<rect x="{cutoff_x:.1f}" y="{pad_t}" width="{future_x-cutoff_x:.1f}" '
                     f'height="{plot_h}" class="forecast-region"/>')

    # horizontal grid lines with price labels
    precision = 6 if span < .1 else (3 if span < 5 else (2 if span < 20 else 0))
    for k in range(5):
        v = lo + (hi - lo) * k / 4
        y = Y(v)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l + plot_w}" y2="{y:.1f}" '
                     f'class="grid"/>')
        parts.append(f'<text x="{pad_l - 8}" y="{y + 4:.1f}" class="axis-label" '
                     f'text-anchor="end">{v:,.{precision}f}</text>')

    # x labels (first / quarter / mid / 3q / last)
    for frac in ((0,0.5,1.0) if forecast else (0,0.25,0.5,0.75,1.0)):
        i = min(int(frac * (n - 1)), n - 1)
        anchor = "start" if frac == 0 else ("end" if frac == 1.0 else "middle")
        parts.append(f'<text x="{X(i):.1f}" y="{height - 8}" class="axis-label" '
                     f'text-anchor="{anchor}">{escape(dates[i][5:])}</text>')

    parts.append(f'<path d="{area}" class="observed-area"/>')
    parts.append(_segments(closes,[X(i) for i in range(n)],[Y(c) for c in closes]))
    if forecast:
        parts.append(f'<line x1="{cutoff_x:.1f}" x2="{cutoff_x:.1f}" y1="{pad_t}" y2="{pad_t+plot_h}" '
                     'class="forecast-cutoff" stroke-dasharray="3 5"/>')
        parts.append(f'<polygon points="{cutoff_x:.1f},{Y(closes[-1]):.1f} {future_x:.1f},{Y(lower):.1f} '
                     f'{future_x:.1f},{Y(upper):.1f}" class="forecast-band"/>')
        parts.append(f'<line x1="{cutoff_x:.1f}" y1="{Y(closes[-1]):.1f}" x2="{future_x:.1f}" y2="{Y(predicted):.1f}" '
                     'class="forecast-line" stroke-width="3" stroke-dasharray="7 5"/>')
        parts.append(f'<line x1="{future_x:.1f}" x2="{future_x:.1f}" y1="{Y(lower):.1f}" y2="{Y(upper):.1f}" '
                     'class="forecast-line" stroke-width="2"/>')
        parts.append(f'<circle cx="{future_x:.1f}" cy="{Y(predicted):.1f}" r="5" class="forecast-point">'
                     f'<title>{escape(translate("Predicción (estimación)"))}: {predicted:,.6f}</title></circle>')
        parts.append(f'<text x="{future_x:.1f}" y="{height-8}" class="axis-label" text-anchor="end">'
                     f'{escape(translate("Siguiente cierre"))}</text>')

    color_by_sentiment = {1: "#198038", -1: "#da1e28", 0: "#8a6c00", None: "#8d8d8d"}
    for idx, sentiment, headline, is_market in markers:
        if not (0 <= idx < n):
            continue
        x, y = X(idx), Y(closes[idx])
        r = 6 if is_market else 5
        label=escape(dates[idx]+' — '+headline, quote=True)
        dot = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color_by_sentiment[sentiment]}" stroke="white" stroke-width="1.5" tabindex="0" aria-label="{label}"><title>{escape(dates[idx])} — {escape(headline)}</title></circle>'
        parts.append(dot)
        if is_market:
            parts.append(f'<line x1="{x:.1f}" y1="{pad_t}" x2="{x:.1f}" y2="{pad_t + plot_h}" '
                         f'stroke="{color_by_sentiment[sentiment]}" stroke-opacity="0.25" '
                         f'stroke-dasharray="4 4"/>')

    parts.append("</svg>")
    result = ''.join(parts)
    if forecast:
        result = f'<div class="forecast-plot" tabindex="0" role="region" aria-label="{escape(label,quote=True)}">{result}</div>'
    return result + _legend(bool(forecast))
