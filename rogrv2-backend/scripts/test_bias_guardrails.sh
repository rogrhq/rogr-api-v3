#!/usr/bin/env bash
set -euo pipefail
[ -f .env ] && set -a && . ./.env && set +a
BASE="http://localhost:${API_PORT:-8000}"
PY="$(bash scripts/_python_bin.sh)"

TOK="$(
  curl -sS -X POST "$BASE/auth/register" \
    -H "Content-Type: application/json" \
    --data-binary '{"email":"bias-guard@rogr.app"}' \
  | "$PY" -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
)"

REQ='{"text":"Austin increased its 2024 city budget by 8%.","test_mode": true}'
curl -sS -o /tmp/bg_body.json \
  -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  --data-binary "$REQ" "$BASE/analyses/preview"

"$PY" - <<'PY'
import json, pathlib, re, sys
d=json.loads(pathlib.Path("/tmp/bg_body.json").read_text() or "{}")
plan=((d.get("methodology") or {}).get("strategy") or {}).get("plan") or {}
arms=(plan.get("arms") or {})
qs=[*(arms.get("A",{}).get("queries") or []), *(arms.get("B",{}).get("queries") or [])]
if not qs: raise SystemExit("No queries present")

DOMAIN_RE = re.compile(r'(?ix)(?:^|[\s\'"])(?:site:|inurl:)?[\w-]+(?:\.[\w-]+)+')
bad=[q for q in qs if DOMAIN_RE.search(q)]
if bad:
    print("BAD QUERIES:", bad)
    raise SystemExit("FAIL: domain-like tokens present in queries")
print("PASS: no domain tokens in queries")
PY