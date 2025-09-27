#!/usr/bin/env bash
set -euo pipefail
# Show which providers will be active if we start the API now
if [ -f .env ]; then set -a; . ./.env; set +a; fi
printf "GOOGLE_CSE_API_KEY: %s\n" "${GOOGLE_CSE_API_KEY:+SET}"
printf "GOOGLE_CSE_ENGINE_ID: %s\n" "${GOOGLE_CSE_ENGINE_ID:+SET}"
printf "BING_API_KEY: %s\n" "${BING_API_KEY:+SET}"
printf "BRAVE_API_KEY: %s\n" "${BRAVE_API_KEY:+SET}"
# Effective status
g_ok=false; b_ok=false; br_ok=false
[ -n "${GOOGLE_CSE_API_KEY:-}" ] && [ -n "${GOOGLE_CSE_ENGINE_ID:-}" ] && g_ok=true
[ -n "${BING_API_KEY:-}" ] && b_ok=true
[ -n "${BRAVE_API_KEY:-}" ] && br_ok=true
echo "Google CSE enabled: $g_ok"
echo "Bing enabled:       $b_ok"
echo "Brave enabled:      $br_ok"