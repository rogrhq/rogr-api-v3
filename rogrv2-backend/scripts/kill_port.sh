#!/usr/bin/env bash
set -euo pipefail
PORT="${1:-8000}"
if command -v lsof >/dev/null 2>&1; then
  PIDS="$(lsof -t -i TCP:${PORT} || true)"
  if [ -n "${PIDS}" ]; then
    echo "Killing processes on :${PORT} -> ${PIDS}"
    kill -9 ${PIDS} || true
  fi
elif command -v fuser >/dev/null 2>&1; then
  fuser -k "${PORT}"/tcp || true
fi