#!/usr/bin/env bash
set -euo pipefail
mask () {
  local v="$1"
  if [ -z "${v:-}" ]; then echo "null"; return; fi
  local n="${#v}"
  if [ "$n" -le 4 ]; then echo "***"; else echo "***${v: -4}"; fi
}
echo "APP_NAME=${APP_NAME:-ROGR API}"
echo "APP_VERSION=${APP_VERSION:-1.0}"
echo "DATABASE_URL=$(mask "${DATABASE_URL:-}")"
echo "AUTH_JWT_SECRET=$(mask "${AUTH_JWT_SECRET:-}")"
echo "CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS:-http://localhost:19006,http://localhost:3000}"
echo "RATE_LIMIT_PER_MINUTE=${RATE_LIMIT_PER_MINUTE:-120}"
echo "GOOGLE_CSE_API_KEY=$(mask "${GOOGLE_CSE_API_KEY:-}")"
echo "GOOGLE_CSE_ENGINE_ID=$(mask "${GOOGLE_CSE_ENGINE_ID:-}")"
echo "BING_API_KEY=$(mask "${BING_API_KEY:-}")"