#!/usr/bin/env bash
set -euo pipefail
[ -f .env ] && set -a && . ./.env && set +a
BASE="http://localhost:${API_PORT:-8000}"
PY="$(bash scripts/_python_bin.sh)"

# Ensure API (single worker is fine)
bash scripts/_ensure_api.sh >/dev/null

# 1) Token
TOK="$(
  curl -sS -X POST "$BASE/auth/register" \
    -H "Content-Type: application/json" \
    --data-binary "{\"email\":\"s2p13@test.rogr\"}" \
  | "$PY" -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))"
)"
[ -n "$TOK" ] || { echo "FAIL: no token"; exit 2; }

# 2) Preview (test_mode to ensure evidence present in baseline)
REQ='{"text":"Austin increased its 2024 city budget by 8%.","test_mode": true}'
RES="$(curl -sS -X POST "$BASE/analyses/preview" -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" --data-binary "$REQ")"
echo "$RES" > /tmp/s2p13.json

# 3) Validate contradiction fields presence and ranges
"$PY" - <<'PY'
import json, pathlib
d=json.loads(pathlib.Path("/tmp/s2p13.json").read_text())
claims=d.get("claims") or []
assert claims, "no claims"
c0=claims[0]
ev=(c0.get("evidence") or {})
guards=(ev.get("guardrails") or {})
cons=(guards.get("consistency") or {})
contra=cons.get("contradiction") or {}
for k in ("pairs_opposed","pairs_total","opposition_ratio","samples"):
    assert k in contra, f"missing contradiction metric: {k}"
assert isinstance(contra["pairs_opposed"], int)
assert isinstance(contra["pairs_total"], int)
assert 0 <= contra["pairs_opposed"] <= contra["pairs_total"]
assert 0.0 <= float(contra["opposition_ratio"]) <= 1.0
assert isinstance(contra["samples"], list)
print("PASS: S2P13 contradiction signals OK")
PY