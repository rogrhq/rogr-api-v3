#!/usr/bin/env bash
set -euo pipefail
[ -f .env ] && set -a && . ./.env && set +a
BASE="http://localhost:${API_PORT:-8000}"
PY="$(bash scripts/_python_bin.sh)"

# 1) get token
TOK="$(
  curl -sS -X POST "$BASE/auth/register" \
    -H "Content-Type: application/json" \
    --data-binary '{"email":"s2-enrich@rogr.app"}' \
  | "$PY" -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
)"

# 2) call preview (test_mode true for speed) and save body for deterministic parsing
curl -sS -D /tmp/s2p1_headers.txt -o /tmp/s2p1_body.json \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  --data-binary '{"text":"Austin increased its 2024 city budget by 8%.","test_mode": true}' \
  "$BASE/analyses/preview"

# 3) validate structure
"$PY" - <<'PY'
import json, pathlib
p = pathlib.Path("/tmp/s2p1_body.json")
d = json.loads(p.read_text() or "{}")
assert isinstance(d.get("claims"), list) and len(d["claims"]) >= 1, "No claims"
c = d["claims"][0]
for k in ("text","tier","entities","numbers","cues","scope","kind_hint"):
    assert k in c, f"missing key on claim: {k}"
nums = c["numbers"]; assert "percents" in nums and isinstance(nums["percents"], list)
cues = c["cues"]; assert isinstance(cues.get("has_comparison"), bool)
print("PASS: S2 Packet 1 enrichment OK")
PY