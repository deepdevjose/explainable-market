"""Server-side SVG charts — no JS/CDN needed, works fully offline."""
from html import escape


def _scale(value, lo, hi, lo_px, hi_px):
    if hi == lo:
        hi = lo + 1
    return lo_px + (value - lo) / (hi - lo) * (hi_px - lo_px)


def sparkline(closes, width=130, height=38):
    if len(closes) < 2:
        return ""
    lo, hi = min(closes), max(closes)
    xs = [ _scale(i, 0, len(closes) - 1, 1, width - 1) for i in range(len(closes)) ]
    ys = [ _scale(c, lo, hi, height - 3, 3) for c in closes ]
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    color = "#198038" if closes[-1] >= closes[0] else "#da1e28"
    return (f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'class="sparkline"><polyline points="{pts}" fill="none" stroke="{color}" '
            f'stroke-width="1.6" stroke-linejoin="round"/></svg>')


def price_chart(dates, closes, markers=None, width=920, height=360, label='Cierres diarios y noticias relacionadas'):
    """Line chart with news markers.

    markers: list of (index, sentiment, headline, is_market) tuples.
    """
    from market_explained.localization import translate
    label = translate(label)
    markers = markers or []
    pad_l, pad_r, pad_t, pad_b = 64, 18, 18, 30
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b
    lo, hi = min(closes), max(closes)
    span = (hi - lo) or 1
    lo -= span * 0.06
    hi += span * 0.06
    n = len(closes)

    def X(i):
        return _scale(i, 0, n - 1, pad_l, pad_l + plot_w)

    def Y(v):
        return _scale(v, lo, hi, pad_t + plot_h, pad_t)

    pts = " ".join(f"{X(i):.1f},{Y(c):.1f}" for i, c in enumerate(closes))
    area = (f"M {X(0):.1f},{pad_t + plot_h} L "
            + " L ".join(f"{X(i):.1f},{Y(c):.1f}" for i, c in enumerate(closes))
            + f" L {X(n - 1):.1f},{pad_t + plot_h} Z")

    parts = [f'<svg viewBox="0 0 {width} {height}" class="price-chart" role="img" aria-label="{escape(label, quote=True)}"><title>{escape(label)}</title>']
    parts.append('<defs><linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">'
                 '<stop offset="0%" stop-color="#0f62fe" stop-opacity="0.12"/>'
                 '<stop offset="100%" stop-color="#0f62fe" stop-opacity="0.01"/>'
                 '</linearGradient></defs>')

    # horizontal grid lines with price labels
    for k in range(5):
        v = lo + (hi - lo) * k / 4
        y = Y(v)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l + plot_w}" y2="{y:.1f}" '
                     f'class="grid"/>')
        parts.append(f'<text x="{pad_l - 8}" y="{y + 4:.1f}" class="axis-label" '
                     f'text-anchor="end">{v:,.0f}</text>')

    # x labels (first / quarter / mid / 3q / last)
    for frac in (0, 0.25, 0.5, 0.75, 1.0):
        i = min(int(frac * (n - 1)), n - 1)
        anchor = "start" if frac == 0 else ("end" if frac == 1.0 else "middle")
        parts.append(f'<text x="{X(i):.1f}" y="{height - 8}" class="axis-label" '
                     f'text-anchor="{anchor}">{dates[i][5:]}</text>')

    parts.append(f'<path d="{area}" fill="url(#areaFill)"/>')
    parts.append(f'<polyline points="{pts}" fill="none" stroke="#0f62fe" '
                 f'stroke-width="2" stroke-linejoin="round"/>')

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
    return "".join(parts)
