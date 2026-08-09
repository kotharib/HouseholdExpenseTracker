#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "==> Starting FastAPI backend on :8000"
(cd server && exec uvicorn app.main:app --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!

cleanup() {
  echo ""
  echo "==> Stopping backend (pid $BACKEND_PID)"
  kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "==> Starting React frontend (Vite) on :5173"
cd frontend
npm run dev
