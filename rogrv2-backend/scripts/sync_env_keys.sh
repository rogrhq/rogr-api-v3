#!/usr/bin/env bash
set -euo pipefail
touch .env .env.example
while IFS= read -r line; do
  case "$line" in
    ""|\#*) continue;;
    *=*)
      key="${line%%=*}"
      grep -q "^${key}=" .env || echo "${key}=" >> .env
      ;;
  esac
done < .env.example
echo "Synced keys from .env.example into .env (left values blank). Edit .env to fill them."