#!/usr/bin/env bash
# S2P7 — Convention-aligned test script
# Purpose:
#   - Ensure API is running (single worker)
#   - Obtain access token via /auth/register
#   - POST /analyses/preview with a sample claim
#   - Validate S2 surface: methodology + enriched claim + verdict present
#
# Usage:
#   bash scripts/test_intel_s2p7.sh
#   CLAIM_TEXT="Water boils at 100C at sea level." TEST_MODE=false bash scripts/test_intel_s2p7.sh

set -euo pipefail

BASE="http://localhost:${API_PORT:-8000}"
PY="$(bash scripts/_python_bin.sh)"
CLAIM_TEXT="${CLAIM_TEXT:-Austin increased its 2024 city budget by 8%.}"
TEST_MODE="${TEST_MODE:-true}"

ensure_api() {
  if ! curl -fsS "$BASE/health/db" >/dev/null 2>&1; then
    API_WORKERS=1 AUTH_JWT_SECRET="${AUTH_JWT_SECRET:-dev-secret}" bash scripts/_start_api_bg.sh
    bash scripts/_wait_ready.sh
  fi
  curl -fsS "$BASE/health/db" >/dev/null
}

get_token() {
  curl -fsS -X POST "$BASE/auth/register" \
    -H "Content-Type: application/json" \
    --data-binary "{\"email\":\"s2p7@rogr.app\"}" \
  | "$PY" - <<'PY'
import sys, json
try:
    d=json.load(sys.stdin)
    print(d.get("access_token",""))
except Exception:
    print("")
PY
}

preview_call() {
  local tok="$1"
  curl -sS -D /tmp/s2p7_headers.txt -o /tmp/s2p7_body.json \
    -H "Authorization: Bearer ${tok}" \
    -H "Content-Type: application/json" \
    -X POST "$BASE/analyses/preview" \
    --data-binary "{\"text\":\"${CLAIM_TEXT}\",\"test_mode\": ${TEST_MODE}}"
  head -1 /tmp/s2p7_headers.txt | sed 's/\r$//'
}

validate_and_print() {
  "$PY" - <<'PY'
import json, pathlib, sys
p = pathlib.Path("/tmp/s2p7_body.json")
raw = p.read_text() if p.exists() else ""
try:
    d = json.loads(raw or "{}")
except Exception as e:
    print("!! JSON parse error:", e)
    print(raw[:400])
    sys.exit(2)

need = {"overall","claims","methodology"}
missing = list(need - set(d.keys()))
if missing:
    print("FAIL: missing keys:", missing); sys.exit(3)

# Light structure checks (won't over-constrain)
ok = True
meth = d.get("methodology") or {}
plan = ((meth.get("strategy") or {}).get("plan")) or {}
arms = set(plan.keys()) if isinstance(plan, dict) else set()
if not ({'A','B'} & arms):
    print("WARN: methodology.strategy.plan missing A/B arms"); ok = False

claims = d.get("claims") or []
if not isinstance(claims, list) or not claims:
    print("FAIL: claims array missing/empty"); sys.exit(4)

c0 = claims[0]
enrich_ok = True
for k in ("text","tier","entities","numbers","cues","scope","kind_hint"):
    if k not in c0:
        print(f"WARN: claim[0] missing {k}"); enrich_ok = False

verdict = c0.get("verdict")
if verdict is None:
    print("FAIL: claim[0] missing verdict"); sys.exit(5)

ev = c0.get("evidence") or {}
A = ev.get("arm_A") or []
B = ev.get("arm_B") or []
# Not required to be non-empty, but present as arrays
if not isinstance(A, list) or not isinstance(B, list):
    print("FAIL: evidence arms not lists"); sys.exit(6)

ov = d.get("overall") or {}
print("# --- S2P7 Summary ---")
print("overall:", {"score": ov.get("score"), "label": ov.get("label")})
print("claims_len:", len(claims))
print("claim[0].tier:", c0.get("tier"))
print("verdict:", {k: verdict.get(k) for k in ("stance","confidence","explanation") if isinstance(verdict, dict)})
print("arm_A items:", len(A), "arm_B items:", len(B))
print("methodology keys:", list(meth.keys())[:6])
print("plan_arms_present:", sorted(list(arms))[:4])
print("enrichment_ok:", enrich_ok)
print("# --- END ---")

if not ok:
    sys.exit(7)
PY
}

main() {
  echo "# Ensuring API…"
  ensure_api

  echo "# Registering…"
  TOK="$(get_token || true)"
  if [ -z "${TOK}" ]; then
    echo "FAIL: no access_token from /auth/register"
    exit 2
  fi

  echo "# Preview (TEST_MODE=${TEST_MODE})…"
  STATUS="$(preview_call "${TOK}")"
  echo "HTTP: ${STATUS}"

  validate_and_print
  echo "PASS: S2P7 verification complete."
}

main