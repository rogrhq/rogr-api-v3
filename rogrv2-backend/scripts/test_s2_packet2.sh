#!/usr/bin/env bash
set -euo pipefail
[ -f .env ] && set -a && . ./.env && set +a
BASE="http://localhost:${API_PORT:-8000}"
PY="$(bash scripts/_python_bin.sh)"

# Start (or ensure) server via orchestrator's convention if not already running
# We rely on the existing orchestrator in RUN_THIS_AFTER_WRITES.sh to start/stop;
# this script only validates behavior.

# 1) Token
TOK="$(
  curl -sS -X POST "$BASE/auth/register" \
    -H "Content-Type: application/json" \
    --data-binary '{"email":"s2-plan@rogr.app"}' \
  | "$PY" -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
)"

# 2) Preview (test_mode true)
REQ='{"text":"Austin increased its 2024 city budget by 8%.","test_mode": true}'
curl -sS -D /tmp/s2p2_headers.txt -o /tmp/s2p2_body.json \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  --data-binary "$REQ" \
  "$BASE/analyses/preview"

# 3) Validate planner v2 and query content
"$PY" - <<'PY'
import json, pathlib, sys
d = json.loads(pathlib.Path("/tmp/s2p2_body.json").read_text() or "{}")
meth = (d.get("methodology") or {})
strategy = (meth.get("strategy") or {})
assert strategy.get("planner") in ("v2","v1"), "missing planner key"
if strategy.get("planner") != "v2":
    raise AssertionError("planner v2 not active")

plan = strategy.get("plan") or {}
arms = plan.get("arms") or {}
A = arms.get("A") or {}
B = arms.get("B") or {}
aq = A.get("queries") or []
bq = B.get("queries") or []
assert aq and bq, "missing queries in arms"

# sanity: at least one query mentions 'Austin' or 'budget' or a percent variant
def has_signal(q: str) -> bool:
    ql = q.lower()
    return any(s in ql for s in ["austin", "budget", "8%", "8 percent", "increase", "year over year", "yoy", "compared to"])

if not any(has_signal(q) for q in aq + bq):
    raise AssertionError("queries missing expected enrichment signals")

print("PASS: S2 Packet 2 planner v2 OK")
PY