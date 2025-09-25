#!/usr/bin/env bash
set -euo pipefail
if [ -x ".venv/bin/python" ]; then echo ".venv/bin/python"; exit 0; fi
if command -v python3.11 >/dev/null 2>&1; then echo "python3.11"; exit 0; fi
echo "python3"