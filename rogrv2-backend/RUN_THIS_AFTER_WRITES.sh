#!/usr/bin/env bash
set -euo pipefail
# Ensure port 8000 is free before running tests that start/expect API
bash scripts/_stop_port_8000.sh || true
# Packet 19 test: request-id propagation + JSON error envelopes
export TEST_CMD="python3 scripts/test_packet19.py"
# Restore friendlier defaults to avoid 429 during export tests
export RATE_LIMIT_PER_MINUTE="${RATE_LIMIT_PER_MINUTE:-120}"
unset MAX_BODY_BYTES || true
bash scripts/_orchestrate.sh