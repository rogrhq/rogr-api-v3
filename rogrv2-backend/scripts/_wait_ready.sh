#!/usr/bin/env bash
set -euo pipefail
for i in {1..25}; do
  if curl -fsS http://localhost:8000/health/db >/dev/null 2>&1; then exit 0; fi
  sleep 1
done
echo "Server not ready after 25s" >&2
exit 1