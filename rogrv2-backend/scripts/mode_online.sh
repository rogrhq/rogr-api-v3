#!/usr/bin/env bash
set -euo pipefail
cat > .mode <<'EOF'
# ONLINE mode: force live gather path for preview
FORCE_LIVE_GATHER=1
EOF
echo "Mode set: ONLINE (FORCE_LIVE_GATHER=1). Restarting API…"
bash scripts/_stop_api_bg.sh || true
bash scripts/_start_api_bg.sh