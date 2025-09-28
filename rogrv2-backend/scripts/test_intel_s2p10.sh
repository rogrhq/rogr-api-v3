#!/usr/bin/env bash
# S2P10 — Source stance balance present & well-formed
set -euo pipefail
[ -f .env ] && set -a && . ./.env && set +a
PY="$(bash scripts/_python_bin.sh)"
BASE="http://localhost:${API_PORT:-8000}"

# 0) health
curl -fsS "$BASE/health/db" >/dev/null

# 1) register
TOK="$(
  curl -sS -H "Content-Type: application/json" \
    -X POST "$BASE/auth/register" \
    --data-binary "{\"email\":\"s2p10@rogr.app\"}" \
  | "$PY" -c 'import sys,json;print(json.load(sys.stdin).get("access_token",""))'
)"
[ -n "$TOK" ] || { echo "FAIL: no token"; exit 2; }

# 2) preview
REQ='{"text":"Austin increased its 2024 city budget by 8%.","test_mode": true}'
OUT="/tmp/s2p10_preview.json"
curl -sS -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -X POST "$BASE/analyses/preview" --data-binary "$REQ" -o "$OUT"

# 3) validate
"$PY" - <<'PY'
import json, pathlib, sys
d=json.loads(pathlib.Path("/tmp/s2p10_preview.json").read_text() or "{}")
claims=d.get("claims") or []
assert claims, "no claims"
ev=(claims[0].get("evidence") or {})
guards=(ev.get("guardrails") or {})
bal=(guards.get("balance") or {})
assert isinstance(bal, dict) and "A" in bal and "B" in bal and "all" in bal, "balance block missing"
for k in ("A","B","all"):
    for kk in ("pro","con","neutral"):
        v=(bal.get(k,{}).get(kk,None))
        assert isinstance(v, int) and v >= 0, f"bad count: {k}.{kk}={v}"
print("PASS: S2P10 stance balance OK")
PY