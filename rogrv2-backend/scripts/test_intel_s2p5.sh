#!/usr/bin/env bash
set -euo pipefail
[ -f .env ] && set -a && . ./.env && set +a
BASE="http://localhost:${API_PORT:-8000}"
PY="$(bash scripts/_python_bin.sh)"

# Ensure server is up (don't start it here; orchestrator or you start it separately)
curl -fsS "$BASE/health/db" >/dev/null

# 1) register and capture exact response to a temp file
RJSON="/tmp/s2p5_register.json"
RHEAD="/tmp/s2p5_register_headers.txt"
curl -sS -D "$RHEAD" -o "$RJSON" \
  -H "Content-Type: application/json" \
  --data-binary '{"email":"s2p5-test@rogr.app"}' \
  "$BASE/auth/register" || true

if [ ! -s "$RJSON" ]; then
  echo "FAIL: /auth/register returned empty body"
  printf "HTTP: "; head -1 "$RHEAD" || true
  exit 2
fi

# Extract token from file (not from a pipe)
TOK="$("$PY" - <<'PY'
import sys, json, pathlib
p = pathlib.Path("/tmp/s2p5_register.json")
try:
    d = json.loads(p.read_text())
    print(d.get("access_token",""))
except Exception as e:
    print("", end="")
PY
)"
if [ -z "$TOK" ]; then
  echo "FAIL: no access_token from /auth/register"
  echo "--- REGISTER HEADERS ---"; head -5 "$RHEAD" || true
  echo "--- REGISTER BODY ---"; sed -n '1,200p' "$RJSON" || true
  exit 3
fi

# 2) call preview (test_mode true)
curl -sS -D /tmp/s2p5_headers.txt -o /tmp/s2p5_body.json \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  --data-binary '{"text":"Austin increased its 2024 city budget by 8%.","test_mode": true}' \
  "$BASE/analyses/preview" || true

# 3) validate JSON shape
"$PY" - <<'PY' || (echo "--- RAW BODY ---"; sed -n "1,200p" /tmp/s2p5_body.json; exit 1)
import json, pathlib, sys
d = json.loads(pathlib.Path("/tmp/s2p5_body.json").read_text() or "{}")
must = ["overall","claims","methodology"]
missing = [k for k in must if k not in d]
if missing:
    print("FAIL: response missing keys:", missing)
    print(json.dumps(d, indent=2))
    sys.exit(3)
if not isinstance(d["claims"], list) or not d["claims"]:
    print("FAIL: claims missing or empty"); sys.exit(4)
ov = d["overall"]
if not isinstance(ov, dict) or "score" not in ov or "label" not in ov:
    print("FAIL: overall missing score/label"); sys.exit(5)
print("PASS: S2P5 response OK")
print("overall:", ov)
print("claims_len:", len(d["claims"]))
PY