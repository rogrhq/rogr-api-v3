#!/usr/bin/env bash
set -euo pipefail

PACKET_ID="P18"
TEST_CMD_DEFAULT="python3 scripts/test_packetP18.py"

echo "[packet:${PACKET_ID}] running: ${TEST_CMD:-$TEST_CMD_DEFAULT}"
if eval "${TEST_CMD:-$TEST_CMD_DEFAULT}"; then
  echo "PACKET PASS ${PACKET_ID}"
else
  echo "PACKET FAIL ${PACKET_ID}"
  exit 1
fi
