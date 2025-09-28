#!/usr/bin/env bash
set -euo pipefail
# Set which test to run; caller may override by exporting TEST_CMD
: "${TEST_CMD:=bash scripts/test_intel_s2p5.sh}"
export TEST_CMD
bash scripts/_orchestrate.sh