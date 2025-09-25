#!/usr/bin/env bash
set -euo pipefail
PY="$(bash scripts/_python_bin.sh)"

# Ensure API is up
curl -fsS http://localhost:8000/health/db >/dev/null

# Register -> tokens
RESP_FILE="$(mktemp)"
CODE="$(curl -sS -w "%{http_code}" -o "$RESP_FILE" \
  -X POST http://localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com"}')"
if [ "$CODE" != "200" ]; then
  echo "FAIL: /auth/register HTTP $CODE"; cat "$RESP_FILE"; rm -f "$RESP_FILE"; exit 1
fi
ACCESS="$("$PY" - <<'PY' "$RESP_FILE" || true
import sys, json, pathlib
p = pathlib.Path(sys.argv[1]).read_text()
print(json.loads(p)["access_token"])
PY
)"
rm -f "$RESP_FILE"
if [ -z "$ACCESS" ]; then echo "FAIL: no access token"; exit 1; fi

# Protected call
RESP_FILE="$(mktemp)"
CODE="$(curl -sS -w "%{http_code}" -o "$RESP_FILE" \
  http://localhost:8000/analyses/healthcheck \
  -H "Authorization: Bearer $ACCESS")"
BODY="$(cat "$RESP_FILE")"
rm -f "$RESP_FILE"

if [ "$CODE" != "200" ]; then
  echo "FAIL: protected route HTTP $CODE"; echo "$BODY"; exit 1
fi
echo "$BODY" | grep -E '"ok"\s*:\s*true' >/dev/null && echo "PASS" || { echo "FAIL: body was: $BODY"; exit 1; }