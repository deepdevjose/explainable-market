"""Backward-compatible WSGI, imports and local executable entry point."""
import sys
from market_explained import application

if __name__ == '__main__':
    application.serve()
else:
    sys.modules[__name__] = application
