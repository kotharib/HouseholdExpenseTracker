#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "Starting FastAPI backend on http://localhost:8000 (docs at /docs)"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
