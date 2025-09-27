#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 --claims \"claim1,claim2,...\" [--outfile outputs/report_YYYYmmdd-HHMMSS.md]"
  exit 1
}

CLAIMS=""
OUTFILE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --claims) shift; CLAIMS="${1:-}";;
    --outfile) shift; OUTFILE="${1:-}";;
    *) echo "Unknown arg: $1"; usage;;
  esac
  shift || true
done
[ -n "$CLAIMS" ] || usage

# Load env + mode
[ -f .env ] && set -a && . ./.env && set +a || true
[ -f .mode ] && set -a && . ./.mode && set +a || true
PORT="${API_PORT:-8000}"
PY="$(bash scripts/_python_bin.sh)"

STAMP="$(date +%Y%m%d-%H%M%S)"
OUTDIR="outputs/batch_${STAMP}"
JSONL="${OUTDIR}/batch.jsonl"
REPORT="${OUTFILE:-outputs/report_${STAMP}.md}"
mkdir -p "${OUTDIR}"

# Get token
TOK="$(
  curl -sS -X POST "http://localhost:${PORT}/auth/register" \
    -H "Content-Type: application/json" \
    --data-binary "{\"email\":\"batch@rogr.app\"}" \
  | "$PY" -c "import sys,json; print(json.load(sys.stdin)['access_token'])"
)"

# Decide test_mode from mode
if [ "${FORCE_LIVE_GATHER:-0}" = "1" ]; then
  TM=false; MODE="online"
else
  TM=true; MODE="offline"
fi

# Split claims
IFS=',' read -r -a ARR <<< "$CLAIMS"

# Call preview for each claim and collect JSON
TMPDIR="$(mktemp -d)"
for idx in "${!ARR[@]}"; do
  claim="${ARR[$idx]}"
  # JSON-escape the claim text safely
  c_json="$(printf '%s' "$claim" | "$PY" -c 'import json,sys; print(json.dumps(sys.stdin.read()))')"

  curl -sS -D "${TMPDIR}/h_${idx}.txt" -o "${TMPDIR}/b_${idx}.json" \
    -H "Authorization: Bearer $TOK" \
    -H "Content-Type: application/json" \
    --data-binary "{\"text\":${c_json},\"test_mode\": ${TM}}" \
    "http://localhost:${PORT}/analyses/preview" >/dev/null || true

  # Append to JSONL
  cat "${TMPDIR}/b_${idx}.json" >> "${JSONL}" || true
  echo >> "${JSONL}"
done

# Produce a single, unified markdown report with both a summary table and per-claim full JSON
"$PY" - <<'PY' "${MODE}" "${REPORT}" "${JSONL}" "${TMPDIR}" "${STAMP}" "${CLAIMS}"
import sys, json, pathlib, textwrap, datetime

MODE, REPORT, JSONL, TMPDIR, STAMP, CLAIMS = sys.argv[1:7]
p_jsonl = pathlib.Path(JSONL)
rows = []
docs = []

# Load each JSON object from JSONL
with p_jsonl.open() as f:
    for line in f:
        line=line.strip()
        if not line: continue
        try:
            d=json.loads(line)
        except Exception:
            d={"_parse_error": line}
        docs.append(d)

def stance_counts(ev):
    s=r=n=0
    for e in (ev or []):
        t=str((e or {}).get("stance","")).lower()
        if t=="support": s+=1
        elif t=="refute": r+=1
        else: n+=1
    return s,r,n

def grade_counts(ev):
    out={}
    for e in (ev or []):
        q=(e or {}).get("quality_letter") or ""
        if q: out[q]=out.get(q,0)+1
    return out

# Build summary rows
for idx, d in enumerate(docs, start=1):
    overall = d.get("overall") or {}
    ev = d.get("evidence") or []
    s,r,n = stance_counts(ev)
    grades = grade_counts(ev)
    rows.append({
        "i": idx,
        "score": int(overall.get("score", 0) or 0),
        "label": str(overall.get("label","")),
        "s": s, "r": r, "n": n,
        "grades": ",".join(f"{k}:{v}" for k,v in sorted(grades.items()))
    })

# Render markdown
md=[]
md.append(f"# ROGR Batch Report — {STAMP}")
md.append("")
md.append(f"**Mode:** `{MODE}`   •   **Claims:** {len(docs)}   •   **Source:** `{JSONL}`")
md.append("")
# Summary table
md.append("| # | Score | Label | s/r/n | Grades |")
md.append("|---:|-----:|:-----:|:-----:|:-------|")
for r in rows:
    md.append(f"| {r['i']} | {r['score']} | {r['label']} | {r['s']}/{r['r']}/{r['n']} | {r['grades']} |")
md.append("")

# Per-claim Truth Capsule sections
for idx, (d, original_claim) in enumerate(zip(docs, [c.strip() for c in CLAIMS.split(',')]), start=1):
    md.append(f"## Claim {idx}: {original_claim}")
    overall = d.get("overall") or {}
    md.append(f"- **Overall:** {int(overall.get('score',0))} — **{overall.get('label','')}**")
    claims_list = d.get("claims") or []
    if claims_list:
        # show up to 5 extracted claim lines (with tier if present)
        md.append("### Extracted Claims")
        for c in claims_list[:5]:
            line = c.get("text") or str(c)
            tier = c.get("tier")
            if tier: md.append(f"- ({tier}) {line}")
            else:    md.append(f"- {line}")
    ev = d.get("evidence") or []
    s=r=n=stance_counts(ev)
    md.append("### Evidence Summary")
    md.append(f"- Items: {len(ev)}   •   Stance: {s}/{r}/{n}")
    grades = grade_counts(ev)
    if grades:
        md.append(f"- Grades: " + ", ".join(f"{k}:{v}" for k,v in sorted(grades.items())))
    # Show up to 8 evidence items (title + url + stance/grade)
    if ev:
        md.append("")
        md.append("| # | Title | Stance | Grade | URL |")
        md.append("|---:|---|:---:|:---:|---|")
        for i,e in enumerate(ev[:8], start=1):
            title = (e.get("title") or "")[:80].replace("|","\\|")
            stance = e.get("stance") or ""
            q = e.get("quality_letter") or ""
            url = e.get("url") or ""
            md.append(f"| {i} | {title} | {stance} | {q} | {url} |")
    # Always include raw JSON for the full Truth Capsule payload
    md.append("")
    md.append("<details><summary>Full JSON</summary>")
    md.append("")
    md.append("```json")
    md.append(json.dumps(d, indent=2, ensure_ascii=False))
    md.append("```")
    md.append("</details>")
    md.append("")

# Write report
pathlib.Path(REPORT).write_text("\n".join(md), encoding="utf-8")
print(f"Wrote unified report -> {REPORT}")
PY

echo "Saved JSONL -> ${JSONL}"
echo "Saved report -> ${REPORT}"