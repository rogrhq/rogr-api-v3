#!/usr/bin/env bash
set -euo pipefail
BASE="http://localhost:${API_PORT:-8000}"
for i in {1..40}; do
  if curl -fsS "${BASE}/health/db" >/dev/null 2>&1; then
    exit 0
  fi
  sleep 0.5
done
echo "Server not ready after timeout" >&2
exit 1