#!/usr/bin/env bash
set -euo pipefail
# Ensure port 8000 is free before running tests that start/expect API
bash scripts/_stop_port_8000.sh || true
# Packet 16 test: security hardening (JSON-only writes, body size limit, 429 rate limit)
export TEST_CMD="python3 scripts/test_packet16.py"
# Lower rate limit + body size for deterministic test behavior
export RATE_LIMIT_PER_MINUTE="5"
export MAX_BODY_BYTES="10240"   # 10 KiB
bash scripts/_orchestrate.sh