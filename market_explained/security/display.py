"""Keep unlicensed Twelve Data observations and derivatives internal by default."""
import os
from flask import has_request_context, request


def twelve_display_allowed() -> bool:
    if os.environ.get('TWELVE_DATA_PUBLIC_DISPLAY')=='1':
        return True
    if not has_request_context():
        return True  # Internal workers; no HTTP response.
    return (request.remote_addr in ('127.0.0.1','::1')
            and not any(name.lower().startswith(('x-forwarded','cf-','forwarded')) for name in request.headers.keys()))


def restricted(instrument_id: str) -> bool:
    return instrument_id.startswith('twelve:') and not twelve_display_allowed()
