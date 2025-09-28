#!/usr/bin/env bash
set -euo pipefail
# Ensure TEST_CMD is exported; default to S2 Packet 1 test when unset
if [ -z "${TEST_CMD:-}" ]; then
  export TEST_CMD="bash scripts/test_s2p2_fix.sh"
fi
bash scripts/_orchestrate.sh