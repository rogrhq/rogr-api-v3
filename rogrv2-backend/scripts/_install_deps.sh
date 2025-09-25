#!/usr/bin/env bash
set -euo pipefail
PY="$(bash scripts/_python_bin.sh)"
"$PY" -m pip install -r requirements.txt