"""Read-only forecast chart anchored to its own source and exact data cutoff."""
from datetime import datetime
from decimal import Decimal

import charts
from market_explained.intelligence.data import series


def prediction_chart(instrument: dict, prediction: dict) -> str | None:
    provider, rows = series(instrument)
    if provider != prediction['provider']:
        return None
    cutoff = datetime.fromisoformat(prediction['data_cutoff_timestamp'])
    history = [r for r in rows if datetime.fromisoformat(r['cutoff']) <= cutoff][-30:]
    # Do not attach an old forecast to newer closes or revised reference prices.
    if (len(history) < 2 or datetime.fromisoformat(history[-1]['cutoff']) != cutoff
            or Decimal(history[-1]['price']) != Decimal(prediction['reference_price'])):
        return None
    return charts.price_chart([r['date'] for r in history],[float(r['price']) for r in history],
        width=700,height=300,label='Cierres observados y predicción',forecast=dict(
            predicted_value=prediction['predicted_value'],
            lower_value=prediction['uncertainty_interval']['lower_value'],
            upper_value=prediction['uncertainty_interval']['upper_value']))
