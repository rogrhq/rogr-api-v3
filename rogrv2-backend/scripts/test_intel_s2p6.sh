#!/usr/bin/env bash
set -euo pipefail

# Load env (API_PORT, etc.)
[ -f .env ] && set -a && . ./.env && set +a
BASE="http://localhost:${API_PORT:-8000}"

PY="$(bash scripts/_python_bin.sh)"
TMPDIR="$(mktemp -d)"
HDR="$TMPDIR/headers.txt"
BODY="$TMPDIR/body.json"
RBODY="$TMPDIR/reg_body.json"
trap 'rm -rf "$TMPDIR"' EXIT

# 1) Health (sanity)
curl -fsS "$BASE/health/db" >/dev/null

# 2) Register and capture token to file then parse via Python (no shell JSON)
curl -fsS -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  --data-binary '{"email":"s2p6-test@rogr.app"}' > "$RBODY"

TOK="$("$PY" - "$RBODY" <<'PY'
import sys, json, pathlib
if len(sys.argv) < 2:
    print("")  # no token
    raise SystemExit(0)
p=pathlib.Path(sys.argv[1])
try:
    d=json.loads(p.read_text())
    print(d.get("access_token",""))
except Exception as e:
    import sys as _s
    _s.stderr.write(f"PARSE_ERROR: {e}\n")
    print("")
PY
)"

if [ -z "${TOK:-}" ]; then
  echo "FAIL: could not parse access_token"
  echo "--- raw register body ---"; sed -n '1,200p' "$RBODY"; echo "-------------------------"
  exit 2
fi

# 3) Call preview (test_mode true to avoid live keys) -> save to file
REQ='{"text":"Austin increased its 2024 city budget by 8%.","test_mode": true}'
curl -sS -D "$HDR" -o "$BODY" \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  --data-binary "$REQ" \
  "$BASE/analyses/preview" >/dev/null || true

# Show status line
printf "HTTP: "; head -1 "$HDR" || true

# 4) Validate JSON from file (never via shell strings)
"$PY" - "$BODY" <<'PY'
import sys, json, pathlib
if len(sys.argv) < 2:
    print("FAIL: missing BODY path")
    raise SystemExit(3)
p=pathlib.Path(sys.argv[1])
try:
    raw = p.read_text()
    d=json.loads(raw if raw.strip() else "{}")
except Exception as e:
    print("FAIL: JSON parse error:", e)
    print("--- RAW BODY ---")
    try:
        print(raw[:2000])
    except Exception:
        print("(no body)")
    raise SystemExit(3)

# Required top-level keys
for k in ("overall","claims","methodology"):
    assert k in d, f"missing key: {k}"

ov = d["overall"]; assert isinstance(ov, dict), "overall must be object"
assert "score" in ov and "label" in ov, "overall missing score/label"

claims = d["claims"]; assert isinstance(claims, list) and len(claims) >= 1, "claims must be non-empty list"
c0 = claims[0]; assert "text" in c0 and "tier" in c0, "claim missing text/tier"
assert "evidence" in c0 and "verdict" in c0, "claim missing evidence/verdict"

# S2 banding present
meth = d["methodology"]; sc = meth.get("scoring", {}); bands = sc.get("bands", {})
assert isinstance(bands, dict) and all(k in bands for k in ("True","Mostly True","Mixed","Mostly False","False")), "bands dictionary incomplete"

print("PASS: S2P6 response OK")
print("overall:", {"score": ov.get("score"), "label": ov.get("label")})
print("claims_len:", len(claims))
PY