#!/usr/bin/env bash
set -euo pipefail
# Ensure port 8000 is free before running tests that start/expect API
bash scripts/_stop_port_8000.sh || true
# Set which test to run here (S1 intelligence baseline)
export TEST_CMD="bash scripts/test_intel_s1.sh"
# Restore friendlier defaults to avoid 429 during export tests
export RATE_LIMIT_PER_MINUTE="${RATE_LIMIT_PER_MINUTE:-120}"
unset MAX_BODY_BYTES || true
bash scripts/_orchestrate.sh