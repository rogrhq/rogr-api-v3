#!/usr/bin/env bash
set -euo pipefail

echo "[packet:P21] running: python3 scripts/test_packetP21.py"
python3 scripts/test_packetP21.py || { echo "PACKET FAIL P21"; exit 1; }
echo "PACKET PASS P21"
