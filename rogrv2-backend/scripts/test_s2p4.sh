#!/usr/bin/env bash
set -euo pipefail
[ -f .env ] && set -a && . ./.env && set +a
BASE="http://localhost:${API_PORT:-8000}"
PY="$(bash scripts/_python_bin.sh)"

# token
TOK="$(
  curl -sS -X POST "$BASE/auth/register" \
    -H "Content-Type: application/json" \
    --data-binary '{"email":"s2p4@test.rogr.app"}' \
  | "$PY" -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
)"

REQ='{"text":"Austin increased its 2024 city budget by 8%.","test_mode": true}'
curl -sS -D /tmp/s2p4_hdr.txt -o /tmp/s2p4_body.json \
  -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  --data-binary "$REQ" "$BASE/analyses/preview"

printf "HTTP: "; head -1 /tmp/s2p4_hdr.txt || true

"$PY" - <<'PY'
import json, pathlib, sys
d=json.loads(pathlib.Path("/tmp/s2p4_body.json").read_text() or "{}")
claims=d.get("claims") or []
assert claims, "no claims"
ev=(((claims[0] or {}).get("evidence") or {}))
a=ev.get("arm_A") or []
b=ev.get("arm_B") or []
meth=(d.get("methodology") or {})
cons=(meth.get("consensus") or {})
for k in ("overlap_ratio","conflict_score","stability"):
    assert k in cons, f"consensus missing {k}"

# Basic dedupe sanity: no exact duplicate (url+title) within an arm
def dupe_free(lst):
    seen=set()
    for x in lst:
        key=(x.get("url",""), x.get("title",""))
        if key in seen: return False
        seen.add(key)
    return True

assert dupe_free(a), "duplicates in arm_A"
assert dupe_free(b), "duplicates in arm_B"

print("PASS: S2P4 consensus metrics present and per-arm dedupe OK")
PY