#!/usr/bin/env bash
set -euo pipefail
PY="$(bash scripts/_python_bin.sh)"
# Keep temp files until script exits so we can debug on failure
trap 'rm -f "${RFILE:-}" "${PFILE:-}" 2>/dev/null || true' EXIT

# 1) Sanity: API up?
curl -fsS http://localhost:8000/health/db >/dev/null || { echo "FAIL: /health/db not reachable"; exit 1; }

# 2) Register and get access token (capture status and body)
RFILE="$(mktemp)"
RCODE="$(curl -sS -w "%{http_code}" -o "$RFILE" -X POST http://localhost:8000/auth/register \
  -H 'Content-Type: application/json' -H 'Accept: application/json' \
  -d '{"email":"me@example.com"}')"
if [ "$RCODE" != "200" ]; then
  echo "FAIL: /auth/register HTTP $RCODE"
  echo "--- body start ---"; cat "$RFILE"; echo; echo "--- body end ---"
  exit 1
fi
ACCESS="$("$PY" -c 'import json,sys; d=json.loads(open(sys.argv[1],"r",encoding="utf-8").read()); print(d.get("access_token",""))' "$RFILE")"
if [ -z "$ACCESS" ]; then
  echo "FAIL: /auth/register returned no access_token"
  echo "--- body start ---"; cat "$RFILE"; echo; echo "--- body end ---"
  exit 1
fi

# 3) Call the protected preview endpoint (test_mode=true, deterministic pipeline)
BODY='{"text":"The mayor says the new bridge will cost $250 million and open in 2027. Officials indicate prior estimates were lower because steel prices rose. Residents claim traffic has doubled since 2020. This announcement follows a year of public hearings.","test_mode":true}'
PFILE="$(mktemp)"
PCODE="$(curl -sS -w "%{http_code}" -o "$PFILE" -X POST http://localhost:8000/analyses/preview \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' -H 'Accept: application/json' \
  -d "$BODY")"
if [ "$PCODE" != "200" ]; then
  echo "FAIL: /analyses/preview HTTP $PCODE"
  echo "--- body start ---"; cat "$PFILE"; echo; echo "--- body end ---"
  exit 1
fi

# 4) Validate shape and required fields
"$PY" - "$PFILE" <<'PY'
import sys, json
data = json.loads(open(sys.argv[1], "r", encoding="utf-8").read())
assert "claims" in data and isinstance(data["claims"], list) and len(data["claims"]) >= 3
first = data["claims"][0]
for k in ("text","tier","priority","strategies","evidence","consensus","score_numeric","label","explanation"):
    assert k in first, f"missing field: {k}"
ov = data.get("overall", {})
assert "score" in ov and "label" in ov
print("PASS")
PY