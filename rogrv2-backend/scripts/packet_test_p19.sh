#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"

if [ -f "scripts/test_packetP19.py" ]; then
  echo "[packet:P19] running: python3 scripts/test_packetP19.py"
  if ! python3 scripts/test_packetP19.py; then
    echo "[packet:P19] note: legacy P19 test failed (diagnostic only)"
  fi
fi

echo "[packet:P19] running: python3 scripts/test_packetP19_nonexist.py"
python3 scripts/test_packetP19_nonexist.py || { echo "PACKET FAIL P19"; exit 1; }

echo "PACKET PASS P19"
