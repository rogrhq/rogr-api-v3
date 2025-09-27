#!/usr/bin/env bash
set -euo pipefail
# Examples:
#   bash scripts/dev_preview.sh --text "Austin increased its 2024 city budget by 8%."
#   BASE="http://127.0.0.1:8000" bash scripts/dev_preview.sh --file note.txt
PY="${PY:-$(bash scripts/_python_bin.sh)}"
exec "$PY" scripts/dev_preview.py "$@"