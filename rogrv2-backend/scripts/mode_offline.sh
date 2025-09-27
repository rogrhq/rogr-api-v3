#!/usr/bin/env bash
set -euo pipefail
cat > .mode <<'EOF'
# OFFLINE mode: do not force live gather
FORCE_LIVE_GATHER=0
EOF
echo "Mode set: OFFLINE (FORCE_LIVE_GATHER=0). Restarting API…"
bash scripts/_stop_api_bg.sh || true
bash scripts/_start_api_bg.sh