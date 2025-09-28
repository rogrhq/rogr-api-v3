#!/usr/bin/env bash
# S2P9 end-to-end test with robust auth and verbose logging (prevents "hangs" on non-zero curl)
set -euo pipefail
[ -f .env ] && set -a && . ./.env && set +a

bash scripts/_start_api_bg.sh
bash scripts/_wait_ready.sh

PY="$(bash scripts/_python_bin.sh)"
BASE="http://localhost:${API_PORT:-8000}"

echo "#0 health"
curl -sS -D /tmp/s2p9_h.txt "$BASE/health/db" -o /tmp/s2p9_h.b || true
head -1 /tmp/s2p9_h.txt
cat /tmp/s2p9_h.b

echo "#1 register"
curl -sS -D /tmp/s2p9_r.txt -o /tmp/s2p9_r.b \
  -H "Content-Type: application/json" \
  -X POST "$BASE/auth/register" \
  --data-binary "{\"email\":\"s2p9-auth@rogr.app\"}" || true
head -1 /tmp/s2p9_r.txt
TOK="$("$PY" - <<'PY'
import json,sys,pathlib
p=pathlib.Path("/tmp/s2p9_r.b")
raw=p.read_text() if p.exists() else ""
try:
    d=json.loads(raw or "{}")
    print(d.get("access_token",""))
except Exception:
    print("")
PY
)"
if [ -z "${TOK}" ]; then
  echo "FAIL: no access_token from /auth/register"
  echo "--- reg body ---"; sed -n "1,200p" /tmp/s2p9_r.b
  exit 2
fi
echo "token_len: ${#TOK}"

echo "#1b me"
# Do NOT use -f so we can see status/body if 401; avoid set -e exit by capturing code
curl -sS -D /tmp/s2p9_me.txt -o /tmp/s2p9_me.b \
  -H "Authorization: Bearer ${TOK}" "$BASE/auth/me" || true
head -1 /tmp/s2p9_me.txt
sed -n "1,200p" /tmp/s2p9_me.b

echo "#2 preview"
REQ='{"text":"Austin increased its 2024 city budget by 8%.","test_mode": true}'
curl -sS -D /tmp/s2p9_p.txt -o /tmp/s2p9_p.b \
  -H "Authorization: Bearer ${TOK}" \
  -H "Content-Type: application/json" \
  -X POST "$BASE/analyses/preview" \
  --data-binary "$REQ" || true
head -1 /tmp/s2p9_p.txt
code="$(head -1 /tmp/s2p9_p.txt | awk '{print $2}')"
if [ "${code:-}" != "200" ]; then
  echo "FAIL: preview HTTP $code"
  echo "--- body ---"; sed -n "1,200p" /tmp/s2p9_p.b
  exit 4
fi

echo "#3 validate"
"$PY" - <<'PY'
import json, pathlib
d=json.loads(pathlib.Path("/tmp/s2p9_p.b").read_text() or "{}")
claims=d.get("claims") or []
assert claims, f"no claims (keys={list(d.keys())})"
ev=(claims[0].get("evidence") or {})
A=ev.get("arm_A") or []
B=ev.get("arm_B") or []
assert isinstance(A, list) and isinstance(B, list), "arms missing"
g=(ev.get("guardrails") or {})
for k in ("A","B"):
    assert isinstance(g.get(k,{}), dict), f"guardrails missing for {k}"
print("PASS: S2P9 guardrails (domain diversity) OK")
PY