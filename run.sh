#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python_bin=venv/bin/python
if [ -x .venv/bin/python ]; then
  python_bin=.venv/bin/python
fi
if [ ! -x "$python_bin" ]; then
  python3 -m venv venv
fi
if ! "$python_bin" -c 'import flask, waitress, websockets, defusedxml' >/dev/null 2>&1; then
  "$python_bin" -m pip install -r requirements.txt
fi
exec "$python_bin" app.py
