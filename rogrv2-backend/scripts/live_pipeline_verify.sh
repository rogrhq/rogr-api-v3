#!/usr/bin/env bash
set -euo pipefail

# S2P30R-AUDIT — One-command live pipeline audit & contract verifier
# Usage:
#   bash scripts/live_pipeline_verify.sh "Your claim text"
#
# Produces artifacts under outputs/fullrun_<timestamp>/ and prints a strict summary.
# Exits non-zero on contract violations.

# 0) Workspace + tools
cd "$(dirname "$0")/.." || exit 1

if ! command -v jq >/dev/null 2>&1; then
  echo "# jq not found; attempting Homebrew install (macOS only)..." >&2
  if command -v brew >/dev/null 2>&1; then brew install jq || true; fi
  command -v jq >/dev/null 2>&1 || { echo "ERROR: jq is required."; exit 2; }
fi

PY_BIN="$(bash scripts/_python_bin.sh 2>/dev/null || echo python3)"
BASE="http://localhost:${API_PORT:-8000}"
CLAIM_INPUT="${1:-Austin increased its 2024 city budget by 8%.}"

STAMP="$(date +%Y%m%d-%H%M%S)"
OUTDIR="outputs/fullrun_${STAMP}"
mkdir -p "$OUTDIR"

# 1) Load .env if present (readonly import)
if [ -f .env ]; then set -a; . ./.env; set +a; fi

echo "# OUTDIR: $OUTDIR"
echo "# CLAIM : $CLAIM_INPUT"

# 2) Prove single production path (no wrappers/rebinds)
"$PY_BIN" -S - <<'PY'
import importlib, inspect, sys
api = importlib.import_module("api.analyses")
core = importlib.import_module("intelligence.pipeline.run")
print("core_path_ok:", api.run_preview is core.run_preview)
print("api.run_preview.module:", api.run_preview.__module__)
print("core.run_preview.module:", core.run_preview.__module__)
PY

# 3) Ensure API up (light health ping; do not auto-start if not present)
HEALTH="$(curl -sS --max-time 3 "$BASE/health/db" || true)"
if ! echo "$HEALTH" | grep -q '"status":"ok"'; then
  echo "ERROR: API not responding at $BASE. Start the API and retry." >&2
  exit 3
fi
echo "# API health: OK"

# 4) Register → token
EMAIL="audit-${STAMP}@rogr.app"
REG="$OUTDIR/register.json"
set +e
curl -sS -o "$REG" -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  --data-binary "{\"email\":\"$EMAIL\"}"
set -e
TOK="$(jq -r '.access_token // empty' "$REG")"
if [ -z "$TOK" ]; then
  echo "ERROR: registration failed or no token. Body:" >&2
  head -c 800 "$REG" >&2; echo >&2
  exit 4
fi
echo "# Registered as $EMAIL"

# 5) Build request body (LIVE)
REQ="$OUTDIR/preview_request.json"
echo "{\"text\": \"${CLAIM_INPUT//\"/\\\"}\", \"test_mode\": false}" > "$REQ"

# 6) Call preview (LIVE)
RESP="$OUTDIR/preview.json"
HTTP_CODE="$(curl -sS -w "%{http_code}" -o "$RESP" \
  -X POST "$BASE/analyses/preview" \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  --data-binary @"$REQ" || true)"
echo "# /analyses/preview HTTP $HTTP_CODE"
if [ "$HTTP_CODE" != "200" ]; then
  echo "ERROR: preview failed. Body:" >&2
  head -c 2000 "$RESP" >&2; echo >&2
  exit 5
fi

# 7) Contract checks & readable summary
SUM="$OUTDIR/preview_summary.json"
"$PY_BIN" -S - "$RESP" "$SUM" <<'PY'
import json, sys, os
resp_path, out_path = sys.argv[1], sys.argv[2]

def fail(msg):
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
    sys.exit(6)

with open(resp_path, "r", encoding="utf-8") as f:
    try:
        d = json.load(f)
    except Exception as e:
        fail(f"response not JSON: {e}")

# Basic presence
claims = d.get("claims") or []
if not claims:
    fail("claims[] missing/empty")

c = claims[0] or {}
text = (c.get("text") or "").strip()
if not text:
    fail("claim text empty")

ev = c.get("evidence") or {}
A = ev.get("arm_A") or []
B = ev.get("arm_B") or []

overall = d.get("overall") or {}
verdict = d.get("verdict") or {}

# Scoring extractors (do not mutate backend, just normalize view)
def rs(it):
    for k in ("rank_score","score","rank"):  # permissive read
        v = it.get(k)
        if isinstance(v,(int,float)):
            return float(v)
    return None

def cs(it):
    v = it.get("credibility_score")
    if isinstance(v,(int,float)):
        return float(v)
    # try meta.credibility.score
    m = it.get("meta") or {}
    cr = m.get("credibility") or {}
    vv = cr.get("score")
    if isinstance(vv,(int,float)):
        return float(vv)
    return None

def contentful(it):
    cc = it.get("content_chars")
    ex = it.get("content_excerpt")
    try:
        if cc is not None and int(cc) > 0:
            return True
    except Exception:
        pass
    return bool(ex)

def top(items, n=3):
    items2 = []
    for it in items:
        items2.append({
            "domain": (it.get("domain") or ""),
            "url": (it.get("url") or ""),
            "rs": rs(it),
            "cs": cs(it),
            "contentful": contentful(it)
        })
    items2.sort(key=lambda z: (z["rs"] if z["rs"] is not None else -1e9,
                               z["cs"] if z["cs"] is not None else -1e9),
                reverse=True)
    return items2[:n]

sumj = {
    "claim_text": text,
    "counts": {"arm_A": len(A), "arm_B": len(B)},
    "top_A": top(A),
    "top_B": top(B),
    "overall": {"score": overall.get("score"), "label": overall.get("label")},
    "verdict": {"label": verdict.get("label"), "confidence": verdict.get("confidence")}
}

# Hard contract checks
viol = []
if not isinstance(A, list): viol.append("arm_A not list")
if not isinstance(B, list): viol.append("arm_B not list")
if sumj["verdict"]["label"] is None: viol.append("verdict.label missing")
vc = sumj["verdict"]["confidence"]
if not (isinstance(vc,(int,float)) and 0 <= vc <= 1): viol.append("verdict.confidence invalid")

# Require at least one content-bearing item per arm (if any items exist at all)
def any_content(items):
    return any(contentful(it) for it in items)

if len(A) > 0 and not any_content(A): viol.append("arm_A has items but none content-bearing")
if len(B) > 0 and not any_content(B): viol.append("arm_B has items but none content-bearing")

# Warn (not fatal) if scores are null across the top set
def all_null_sc(items):
    return all(z["rs"] is None and z["cs"] is None for z in items)

sumj["warnings"] = []
if all_null_sc(sumj["top_A"]): sumj["warnings"].append("top_A rs/cs all null")
if all_null_sc(sumj["top_B"]): sumj["warnings"].append("top_B rs/cs all null")

ok = (len(viol) == 0)
sumj["ok"] = ok
sumj["violations"] = viol

with open(out_path, "w", encoding="utf-8") as w:
    json.dump(sumj, w, ensure_ascii=False, indent=2)

print(json.dumps(sumj, ensure_ascii=False, indent=2))
if not ok: sys.exit(7)
PY

echo
echo "# SUMMARY written to: $SUM"
echo "# DONE"
