#!/usr/bin/env bash
set -euo pipefail
: "${TEST_CMD:?TEST_CMD not set}"
PY="$(bash scripts/_python_bin.sh)"
bash scripts/_install_deps.sh
bash scripts/_start_api_bg.sh || true
bash scripts/_wait_ready.sh || true
set +e
TEST_CMD="${TEST_CMD//python3 /$PY }"
eval "$TEST_CMD"
code=$?
set -e
bash scripts/_stop_api_bg.sh
exit $code