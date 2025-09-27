#!/usr/bin/env bash
set -euo pipefail
: "${AUTH_JWT_SECRET:=dev-secret-$(date +%s)}"
# Load .env if present
if [ -f .env ]; then set -a; . ./.env; set +a; fi
# Optional mode overlay (persists ONLINE/OFFLINE)
if [ -f .mode ]; then set -a; . ./.mode; set +a; fi
PORT="${API_PORT:-8000}"
# If a healthy server is already up, do nothing
if curl -fsS "http://localhost:${PORT}/health/ready" >/dev/null 2>&1; then
  echo "API already running on :${PORT}"
  exit 0
fi
# If a PID file exists but process is gone, clean it
if [ -f .api_pid ] && ! ps -p "$(cat .api_pid 2>/dev/null)" >/dev/null 2>&1; then
  rm -f .api_pid
fi
# Start
(uvicorn main:app --host 0.0.0.0 --port "${PORT}" --workers 2 & echo $! > .api_pid)
echo "Started API on :${PORT} (pid $(cat .api_pid))"