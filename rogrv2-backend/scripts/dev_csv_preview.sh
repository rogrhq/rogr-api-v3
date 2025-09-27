#!/usr/bin/env bash
set -euo pipefail
# Example:
#   bash scripts/dev_csv_preview.sh --claims "Austin increased...,The earth has two moons."
PY="${PY:-$(bash scripts/_python_bin.sh)}"
exec "$PY" scripts/dev_csv_preview.py "$@"