#!/usr/bin/env bash
set -euo pipefail

# Load env (API_PORT, etc.)
if [ -f .env ]; then set -a; . ./.env; set +a; fi
BASE="http://localhost:${API_PORT:-8000}"
PY="$(bash scripts/_python_bin.sh)"

echo "# Ensuring API health…"
curl -fsS "$BASE/health/db" >/dev/null

echo "# Registering…"
curl -sS -D /tmp/s2p7_reg.h -o /tmp/s2p7_reg.json \
  -H "Content-Type: application/json" \
  -X POST "$BASE/auth/register" \
  --data-binary "{\"email\":\"s2p7@rogr.app\"}" >/dev/null || true

TOK="$("$PY" - <<'PY'
import json, pathlib, sys
p = pathlib.Path("/tmp/s2p7_reg.json")
try:
    d = json.loads(p.read_text() or "{}")
    print(d.get("access_token",""))
except Exception as e:
    print("")
PY
)"

if [ -z "$TOK" ]; then
  echo "FAIL: no access_token from /auth/register"
  echo "---- headers ----"; sed -n '1,80p' /tmp/s2p7_reg.h || true
  echo "---- body ----"; sed -n '1,200p' /tmp/s2p7_reg.json || true
  exit 2
fi

echo "# Preview (test_mode=true)…"
curl -sS -D /tmp/s2p7_prev.h -o /tmp/s2p7_prev.json \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -X POST "$BASE/analyses/preview" \
  --data-binary "{\"text\":\"Austin increased its 2024 city budget by 8%.\",\"test_mode\": true}" >/dev/null || true

"$PY" - <<'PY'
import json, pathlib, sys
d = json.loads(pathlib.Path("/tmp/s2p7_prev.json").read_text() or "{}")
keys = set(d.keys())
need = {"overall","claims","methodology"}
missing = list(need - keys)
if missing:
    print("FAIL: preview missing keys:", missing)
    print("---- body ----")
    print(json.dumps(d, indent=2)[:1000])
    sys.exit(3)
print("PASS: S2P7")
print("overall:", d.get("overall"))
print("claims_len:", len(d.get("claims",[])))
PY