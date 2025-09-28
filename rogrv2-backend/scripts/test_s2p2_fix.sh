#!/usr/bin/env bash
set -euo pipefail
[ -f .env ] && set -a && . ./.env && set +a
BASE="http://localhost:${API_PORT:-8000}"
PY="$(bash scripts/_python_bin.sh)"

# 1) token
TOK="$(
  curl -sS -X POST "$BASE/auth/register" -H "Content-Type: application/json" \
    --data-binary '{"email":"s2p2-fix@rogr.app"}' \
  | "$PY" -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
)"

# 2) preview
curl -sS -D /tmp/s2p2_hdr.txt -o /tmp/s2p2_body.json \
  -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  --data-binary '{"text":"Austin increased its 2024 city budget by 8%.","test_mode": true}' \
  "$BASE/analyses/preview"

printf "HTTP: "; head -1 /tmp/s2p2_hdr.txt
"$PY" - <<'PY'
import json, pathlib, sys
d=json.loads(pathlib.Path("/tmp/s2p2_body.json").read_text() or "{}")
meth=((d.get("methodology") or {}).get("strategy") or {})
plan=meth.get("plan") or {}
assert isinstance(plan, dict), "plan must be a dict"
arms=(plan.get("arms") or {})
assert "A" in arms and "B" in arms, "plan.arms must contain A and B"
print("PASS: methodology.strategy.plan present with A/B arms")
PY