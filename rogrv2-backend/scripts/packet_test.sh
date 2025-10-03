#!/usr/bin/env bash
set -euo pipefail
: "${PACKET_ID:=P14}"
: "${PACKET_TIMEOUT:=120}"
: "${TEST_CMD_DEFAULT:=python3 scripts/test_packet${PACKET_ID}.py}"

# LIVE ONLY: no mocks. If .env exists, the test script loads it automatically.

echo "[packet:${PACKET_ID}] running: ${TEST_CMD:-$TEST_CMD_DEFAULT}"
if eval "${TEST_CMD:-$TEST_CMD_DEFAULT}"; then
  echo "PACKET PASS ${PACKET_ID}"
else
  echo "PACKET FAIL ${PACKET_ID}"
  exit 1
fi

# Run stricter contract/regression checks for P14 (does not replace the main test)
echo "[packet:${PACKET_ID}] running: python3 scripts/test_packet${PACKET_ID}_strict.py"
if python3 "scripts/test_packet${PACKET_ID}_strict.py"; then
  echo "PACKET PASS ${PACKET_ID}-STRICT"
  exit 0
else
  echo "PACKET FAIL ${PACKET_ID}-STRICT"
  exit 1
fi
