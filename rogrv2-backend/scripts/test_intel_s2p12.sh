#!/usr/bin/env bash
set -euo pipefail
[ -f .env ] && set -a && . ./.env && set +a
BASE="http://localhost:${API_PORT:-8000}"
PY="$(bash scripts/_python_bin.sh)"

# Ensure API
bash scripts/_start_api_bg.sh
bash scripts/_wait_ready.sh

# 1) Register → token
TOK="$(
  curl -sS -X POST "$BASE/auth/register" \
    -H "Content-Type: application/json" \
    --data-binary "{\"email\":\"s2p12@test.rogr\"}" \
  | "$PY" -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))"
)"
[ -n "$TOK" ] || { echo "FAIL: no token"; exit 2; }

# 2) Call preview (test_mode to guarantee seeded evidence if needed)
REQ='{"text":"Austin increased its 2024 city budget by 8%.","test_mode": true}'
RES="$(curl -sS -X POST "$BASE/analyses/preview" -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" --data-binary "$REQ")"
echo "$RES" > /tmp/s2p12.json

# 3) Validate agreement metrics exist and are well-formed
"$PY" - <<'PY'
import json, sys, pathlib
d=json.loads(pathlib.Path("/tmp/s2p12.json").read_text())
claims=d.get("claims") or []
assert claims, "no claims"
c0=claims[0]
ev=(c0.get("evidence") or {})
guards=(ev.get("guardrails") or {})
agree=guards.get("agreement") or {}
for k in ("token_overlap_jaccard","shared_domains","exact_url_matches"):
    assert k in agree, f"missing agreement metric: {k}"
assert isinstance(agree["token_overlap_jaccard"], (int,float)), "jacc must be number"
assert 0.0 <= float(agree["token_overlap_jaccard"]) <= 1.0, "jacc out of range"
print("PASS: S2P12 agreement signals OK")
PY