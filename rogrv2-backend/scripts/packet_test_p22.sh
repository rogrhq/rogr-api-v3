#!/usr/bin/env bash
set -euo pipefail
# P22 test driver
# Ensures we're at repo root and Python sees it
if [[ ! -f "main.py" ]]; then
  echo "P22 FAIL: run from repo root containing main.py" >&2
  exit 1
fi

# Prefer local venv if present
PYBIN="${PYBIN:-python3}"
if [[ -f ".venv/bin/python3" ]]; then
  PYBIN=".venv/bin/python3"
fi

# Ensure sitecustomize is loadable by being on sys.path (CWD inserted by Python)
ROGR_DIAG=1 "${PYBIN}" scripts/test_packetP22.py
