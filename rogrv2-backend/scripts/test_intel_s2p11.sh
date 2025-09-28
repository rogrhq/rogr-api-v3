#!/usr/bin/env bash
# S2P11 — Credibility scores per item + rollup present
set -euo pipefail
[ -f .env ] && set -a && . ./.env && set +a
PY="$(bash scripts/_python_bin.sh)"
BASE="http://localhost:${API_PORT:-8000}"

# health
curl -fsS "$BASE/health/db" >/dev/null

# register
TOK="$(
  curl -sS -H "Content-Type: application/json" \
    -X POST "$BASE/auth/register" \
    --data-binary "{\"email\":\"s2p11@rogr.app\"}" \
  | "$PY" -c 'import sys,json;print(json.load(sys.stdin).get("access_token",""))'
)"
[ -n "$TOK" ] || { echo "FAIL: no token"; exit 2; }

# preview
REQ='{"text":"Austin increased its 2024 city budget by 8%.","test_mode": true}'
OUT="/tmp/s2p11_preview.json"
curl -sS -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -X POST "$BASE/analyses/preview" --data-binary "$REQ" -o "$OUT"

# validate
"$PY" - <<'PY'
import json, pathlib
d=json.loads(pathlib.Path("/tmp/s2p11_preview.json").read_text() or "{}")
claims=d.get("claims") or []
assert claims, "no claims"
ev=claims[0].get("evidence") or {}
A=ev.get("arm_A") or []
B=ev.get("arm_B") or []
assert isinstance(A, list) and isinstance(B, list), "arms missing"
def _check(items):
    ok_any=False
    for it in items:
        meta=(it.get("meta") or {})
        cred=(meta.get("credibility") or {})
        if isinstance(cred.get("score"), int):
            ok_any=True
            det=cred.get("details") or {}
            assert all(k in det for k in ("base_from_type","tld_bonus","recency_bonus","snippet_adjust")), "missing cred details"
    return ok_any
assert _check(A) or _check(B), "no credibility scores on items"
guards=(ev.get("guardrails") or {})
cred=guards.get("credibility") or {}
assert isinstance(cred.get("avg",{}).get("all",0), int), "missing credibility rollup"
print("PASS: S2P11 credibility scoring OK")
PY