#!/usr/bin/env bash
set -euo pipefail

BASE_URL="http://localhost:${API_PORT:-8000}"
PY="$(bash scripts/_python_bin.sh)"

# 1) Register to get a fresh JWT (no external env needed)
TOK="$(
  curl -sS -X POST "${BASE_URL}/auth/register" \
    -H "Content-Type: application/json" \
    --data-binary '{"email":"s1-test@rogr.app"}' \
  | "$PY" -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
)"

if [ -z "${TOK:-}" ]; then
  echo "FAIL: could not obtain access_token from /auth/register" >&2
  exit 1
fi

# 2) Call preview with a known sentence (S1 focus is pipeline wiring + strategy hooks)
REQ_BODY='{"text":"Austin increased its 2024 city budget by 8%.","test_mode": true}'
curl -sS -D /tmp/s1_headers.txt -o /tmp/s1_body.json \
  -H "Authorization: Bearer ${TOK}" \
  -H "Content-Type: application/json" \
  --data-binary "${REQ_BODY}" \
  "${BASE_URL}/analyses/preview" || true

# 3) Validate shape & print a compact summary
"$PY" - <<'PY'
import json, pathlib, sys
p = pathlib.Path("/tmp/s1_body.json")
try:
    d = json.loads(p.read_text() or "{}")
except Exception as e:
    print("FAIL: response not JSON:", e, file=sys.stderr)
    print("--- RAW BODY ---")
    print(p.read_text() if p.exists() else "(missing)")
    sys.exit(1)

# Minimal assertions for S1
if "overall" not in d or "claims" not in d:
    print("FAIL: missing keys; have:", list(d.keys()))
    sys.exit(1)

claims = d.get("claims") or []
overall = d.get("overall") or {}
print("PASS: S1 baseline OK")
print("  overall:", overall)
print("  claims:", len(claims))
# show first claim's scaffold if present
if claims:
    c0 = claims[0]
    keys = ["text","tier","strategy","evidence","verdict","explanation"]
    view = {k: c0.get(k) for k in keys if k in c0}
    print("  first_claim:", {k:v for k,v in view.items() if v is not None})
PY