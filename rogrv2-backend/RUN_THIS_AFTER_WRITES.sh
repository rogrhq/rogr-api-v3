#!/usr/bin/env bash
set -euo pipefail
# Ensure port 8000 is free before running tests that start/expect API
bash scripts/_stop_port_8000.sh || true
# Packet 15 test: mobile endpoints (preview/commit/feed/archive/jobs)
export TEST_CMD="python3 scripts/test_packet15.py"
bash scripts/_orchestrate.sh