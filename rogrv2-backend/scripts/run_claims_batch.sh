#!/usr/bin/env bash
set -euo pipefail
usage(){ echo "Usage: $0 --claims \"claim1,claim2,...\" [--outfile outputs/latest_batch.jsonl]"; exit 1; }
CLAIMS=""; OUT=""; while [ $# -gt 0 ]; do
  case "$1" in
    --claims) shift; CLAIMS="${1:-}";;
    --outfile) shift; OUT="${1:-}";;
    *) echo "Unknown arg: $1"; usage;;
  esac; shift || true
done
[ -n "$CLAIMS" ] || usage
OUT="${OUT:-outputs/batch_$(date +%Y%m%d-%H%M%S)/batch.jsonl}"
mkdir -p "$(dirname "$OUT")"

# Load .env + .mode for local curl/PY tools
[ -f .env ] && set -a && . ./.env && set +a || true
[ -f .mode ] && set -a && . ./.mode && set +a || true
PORT="${API_PORT:-8000}"
PY="$(bash scripts/_python_bin.sh)"

# 1) Token
TOK="$(
  curl -sS -X POST "http://localhost:${PORT}/auth/register" \
    -H "Content-Type: application/json" \
    --data-binary "{\"email\":\"batch@rogr.app\"}" \
  | "$PY" -c "import sys,json; print(json.load(sys.stdin)['access_token'])"
)"

# 2) Run each claim
IFS=',' read -r -a ARR <<< "$CLAIMS"
TABLE="$(mktemp)"; : > "$TABLE"
printf "#   %-60s  %-7s  %-6s  %-10s  %-10s  %s\n" "claim" "score" "label" "ev s/r/n" "grades" "mode" >> "$TABLE"
printf -- "------------------------------------------------------------------------------------------------------------------------------------------\n" >> "$TABLE"

for i in "${!ARR[@]}"; do
  c="${ARR[$i]}"; c_json=$(printf '%s' "$c" | "$PY" -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
  # Decide test_mode from FORCE_LIVE_GATHER (1 => test_mode=false)
  if [ "${FORCE_LIVE_GATHER:-0}" = "1" ]; then TM=false; MODE="online"; else TM=true; MODE="offline"; fi
  curl -sS -D /tmp/h.txt -o /tmp/b.json \
    -H "Authorization: Bearer $TOK" \
    -H "Content-Type: application/json" \
    --data-binary "{\"text\":${c_json},\"test_mode\": ${TM}}" \
    "http://localhost:${PORT}/analyses/preview" >/dev/null || true

  # Append full JSON line to outfile
  cat /tmp/b.json >> "$OUT"
  echo >> "$OUT"

  # Summarize for table
  IDX="$((i+1))" CLAIM="$c" MODE="$MODE" "$PY" - <<'PY' >> "$TABLE"
import json,sys,os
with open("/tmp/b.json","r") as fh:
    d=json.load(fh)
ov=d.get("overall") or {}
ev=d.get("evidence") or []
s=r=n=0
for e in ev:
    t=(e or {}).get("stance","").lower()
    if t=="support": s+=1
    elif t=="refute": r+=1
    else: n+=1
grades={}
for e in ev:
    q=(e or {}).get("quality_letter") or ""
    if q: grades[q]=grades.get(q,0)+1
glist=",".join(f"{k}:{v}" for k,v in sorted(grades.items()))
# The shell adds index/claim/mode as env vars for readability
idx=os.environ.get("IDX","?"); claim=os.environ.get("CLAIM",""); mode=os.environ.get("MODE","")
print("{:<3} {:<60}  {:<7}  {:<6}  {}/{}/{}   {:<10}  {}".format(
    idx, (claim[:60]), int(ov.get("score",0) or 0), str(ov.get("label","") or ""),
    s,r,n, glist, mode))
PY
done

cat "$TABLE"
echo
echo "Saved full results -> ${OUT}"