#!/usr/bin/env bash
set -euo pipefail
if [ -f .api_pid ]; then
  kill "$(cat .api_pid)" 2>/dev/null || true
  rm -f .api_pid
fi