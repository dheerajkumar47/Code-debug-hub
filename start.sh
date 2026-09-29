#!/usr/bin/env bash
# BidSmith one-click start (macOS / Linux):  ./start.sh
set -e
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "Install Python 3.11+ first: https://www.python.org/downloads/"; exit 1; }
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
python -m pip install -q --disable-pip-version-check -r requirements.txt
if [ ! -f .env ] || [ -f keys.txt ]; then
  echo; echo "=== First-time setup: paste your 2 keys ==="
  python -m bidsmith setup
fi
python -m bidsmith check || { echo; echo "Fix the ❌ lines. Re-enter keys with: python -m bidsmith setup"; exit 1; }
exec python -m bidsmith serve
