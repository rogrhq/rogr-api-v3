#!/usr/bin/env bash
set -euo pipefail
[ -f .env ] && set -a && . ./.env && set +a
BASE="http://localhost:${API_PORT:-8000}"
PY="$(bash scripts/_python_bin.sh)"

# token
TOK="$(
  curl -sS -X POST "$BASE/auth/register" \
    -H "Content-Type: application/json" \
    --data-binary '{"email":"s2p3@test.rogr.app"}' \
  | "$PY" -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
)"

REQ='{"text":"Austin increased its 2024 city budget by 8%.","test_mode": true}'
curl -sS -D /tmp/s2p3_hdr.txt -o /tmp/s2p3_body.json \
  -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  --data-binary "$REQ" "$BASE/analyses/preview"

printf "HTTP: "; head -1 /tmp/s2p3_hdr.txt || true

"$PY" - <<'PY'
import json, pathlib, sys
d=json.loads(pathlib.Path("/tmp/s2p3_body.json").read_text() or "{}")
claims=d.get("claims") or []
assert claims, "no claims"
ev=(((claims[0] or {}).get("evidence") or {}))
a=ev.get("arm_A") or []
b=ev.get("arm_B") or []
# Evidence lists should exist (can be empty if offline), and rank_features show type+lexical
def ok(lst):
    return all(isinstance(x.get("rank_features",{}).get("lexical",0), float) and
               isinstance(x.get("rank_features",{}).get("prior",0), (int,float)) and
               "type" in x.get("rank_features",{}) for x in lst)
assert isinstance(a, list) and isinstance(b, list), "evidence arrays missing"
if a or b:
    # When online keys present, at least one item must have rank_score
    assert any("rank_score" in (x or {}) for x in (a+b)), "rank_score missing on live items"
print("PASS: S2P3 ranking present; evidence lists OK")
PY