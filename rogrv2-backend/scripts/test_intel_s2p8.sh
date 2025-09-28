#!/usr/bin/env bash
set -euo pipefail
[ -f .env ] && set -a && . ./.env && set +a

# 0) Ensure deps (no-op if already installed)
bash scripts/_install_deps.sh >/dev/null 2>&1 || true

# 1) Start API if not running
bash scripts/_start_api_bg.sh
bash scripts/_wait_ready.sh

BASE="http://localhost:${API_PORT:-8000}"
PY="$(bash scripts/_python_bin.sh)"

# 2) Register → token
TOK="$(
  curl -sS -X POST "$BASE/auth/register" \
    -H "Content-Type: application/json" \
    --data-binary '{"email":"s2p8@test.rogr"}' \
  | "$PY" -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
)"

# 3) Preview a normal claim (test_mode true for deterministic branch)
REQ='{"text":"Austin increased its 2024 city budget by 8%.","test_mode": true}'
curl -sS -X POST "$BASE/analyses/preview" \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  --data-binary "$REQ" \
  -o /tmp/s2p8_preview.json

# 4) Validate policy annotation presence and basic types
"$PY" - <<'PY'
import json,sys,pathlib
d=json.loads(pathlib.Path("/tmp/s2p8_preview.json").read_text() or "{}")
assert "methodology" in d, "missing methodology"
pol = (d.get("methodology") or {}).get("policy")
assert isinstance(pol, dict), "missing methodology.policy"
for k in ("min_length_ok","max_length_ok","safe_to_process"):
    assert isinstance(pol.get(k), bool), f"policy field {k} not bool"
for k in ("length","rough_tokens","max_chars_limit","min_chars_limit"):
    assert isinstance(pol.get(k), int), f"policy field {k} not int"
assert isinstance(pol.get("ambiguity_flags",[]), list), "policy.ambiguity_flags not list"
print("PASS: S2P8 policy annotation OK")
PY