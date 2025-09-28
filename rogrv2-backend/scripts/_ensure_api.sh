#!/usr/bin/env bash
set -euo pipefail

# Load local env if present (API_PORT, AUTH_JWT_SECRET, etc.)
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

PORT="${API_PORT:-8000}"

# If API is already healthy, exit fast
if curl -fsS "http://localhost:${PORT}/health/db" >/dev/null 2>&1; then
  exit 0
fi

# Ensure nothing is bound on the port; clear old pid file if any
lsof -ti tcp:"${PORT}" | xargs -r kill -9 || true
pkill -9 -f "uvicorn.*main:app" || true
rm -f .api_pid || true

# Start single worker with a default secret for local/dev
: "${API_WORKERS:=1}"
: "${AUTH_JWT_SECRET:=dev-secret}"
API_WORKERS="${API_WORKERS}" AUTH_JWT_SECRET="${AUTH_JWT_SECRET}" bash scripts/_start_api_bg.sh

# Wait until ready
bash scripts/_wait_ready.sh

# Final health check (propagate non-zero on failure)
curl -fsS "http://localhost:${PORT}/health/db" >/dev/null