#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://localhost:8000}"
echo "Ready:" && curl -fsS "$BASE/health/ready"; echo
PY="${PY:-$(bash scripts/_python_bin.sh)}"
curl -fsS -X POST "$BASE/auth/register" -H "Content-Type: application/json" -d "{\"email\":\"sanity@example.com\"}" > debug_sanity_reg.json
ACCESS="$("$PY" - <<PY
import json, pathlib; p=pathlib.Path("debug_sanity_reg.json"); print(json.loads(p.read_text())["access_token"])
PY
)"
echo "Token: ${#ACCESS} chars"
curl -fsS -X POST "$BASE/analyses/preview" -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json" -d "{\"text\":\"Austin increased its 2024 city budget by 8%.\",\"test_mode\":true}" > debug_sanity_preview.json
"$PY" - <<PY
import json, pathlib; d=json.loads(pathlib.Path("debug_sanity_preview.json").read_text()); print({"overall":d.get("overall"), "claims_len":len(d.get("claims",[]))})
PY
curl -fsS "$BASE/metrics" > debug_sanity_metrics.json
"$PY" - <<PY
import json, pathlib; m=json.loads(pathlib.Path("debug_sanity_metrics.json").read_text()); print({"requests_total":m.get("requests_total"),"status_2xx":m.get("status_2xx"),"in_flight":m.get("in_flight")})
PY