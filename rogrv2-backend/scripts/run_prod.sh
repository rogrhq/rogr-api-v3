#!/usr/bin/env bash
set -euo pipefail
# Minimal production runner (single worker due to in-proc queue in MVP)
: "${AUTH_JWT_SECRET:?AUTH_JWT_SECRET not set}"
: "${DATABASE_URL:=${DATABASE_URL:-sqlite+aiosqlite:///$PWD/rogr_dev.db}}"
export AUTH_JWT_SECRET DATABASE_URL
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1