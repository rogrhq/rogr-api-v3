#!/usr/bin/env bash
set -euo pipefail
: "${TEST_CMD:=bash scripts/test_intel_s2p8.sh}"
: "${API_WORKERS:=1}"
bash scripts/_install_deps.sh
bash scripts/_start_api_bg.sh || true
bash scripts/_wait_ready.sh || true
set +e
eval "$TEST_CMD"
code=$?
set -e
bash scripts/_stop_api_bg.sh
exit $code