#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
export ROGR_DIAG_P20=1

echo "[packet:P20] running: python3 scripts/test_packetP20.py"
python3 scripts/test_packetP20.py || { echo "PACKET FAIL P20"; exit 1; }

echo "PACKET PASS P20"
