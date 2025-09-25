#!/usr/bin/env bash
set -euo pipefail
# Ensure port 8000 is free before running tests that start/expect API
bash scripts/_stop_port_8000.sh || true
export TEST_CMD="bash scripts/test_packet7.sh"
bash scripts/_orchestrate.sh