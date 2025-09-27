#!/usr/bin/env python3
"""
CSV batch preview runner.
- Registers ONCE (email -> token)
- Splits --claims by comma (CSV-ish: commas split; surrounding spaces trimmed)
- Calls /analyses/preview for each claim, test_mode by default
- Prints a compact summary table
- Saves each full result under outputs/batch_<ts>/claim_<n>.json

Usage examples:
  BASE=http://localhost:8000 python3 scripts/dev_csv_preview.py --claims "Claim A, Claim B"
  python3 scripts/dev_csv_preview.py --claims "Austin increased...,The earth has two moons."
  python3 scripts/dev_csv_preview.py --claims "C1, C2" --email investor@example.com --no-test-mode
"""
from __future__ import annotations
import os, sys, json, argparse, datetime, pathlib, urllib.request

BASE = os.environ.get("BASE", "http://localhost:8000")

def _req(method: str, path: str, data=None, headers=None):
    url = f"{BASE}{path}"
    hdrs = {} if headers is None else dict(headers)
    body = None
    if data is not None:
        hdrs["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    with urllib.request.urlopen(req, timeout=90) as resp:
        raw = resp.read().decode("utf-8")
        return resp.getcode(), json.loads(raw)

def register(email: str) -> str:
    code, body = _req("POST", "/auth/register", {"email": email})
    if code != 200 or "access_token" not in body:
        raise RuntimeError(f"register failed: {code} {body}")
    return body["access_token"]

def preview(token: str, text: str, test_mode: bool=True) -> dict:
    code, body = _req("POST", "/analyses/preview",
                      {"text": text, "test_mode": test_mode},
                      headers={"Authorization": f"Bearer {token}"})
    if code != 200:
        raise RuntimeError(f"preview failed: {code} {body}")
    return body

def _split_claims(s: str) -> list[str]:
    # Simple CSV split on ',' and strip spaces. Empty entries removed.
    # (If you ever need quoted CSV with commas inside quotes, we can upgrade to csv module.)
    return [part.strip() for part in s.split(",") if part.strip()]

def _evidence_summary(data: dict) -> dict:
    # Works with our API's evidence shape if present; otherwise returns zeros.
    ev = data.get("evidence") or []  # some responses may include claim-level evidence; others at top
    if isinstance(ev, dict):
        # sometimes evidence keyed by claim id/tier
        all_items = []
        for v in ev.values():
            if isinstance(v, list): all_items.extend(v)
        ev = all_items
    sup = sum(1 for e in ev if str(e.get("stance","")).lower()=="support")
    ref = sum(1 for e in ev if str(e.get("stance","")).lower()=="refute")
    neu = sum(1 for e in ev if str(e.get("stance","")).lower()=="neutral")
    grades = {}
    for e in ev:
        g = (e.get("quality_letter") or "").upper()
        if g: grades[g] = grades.get(g,0)+1
    return {"support":sup,"refute":ref,"neutral":neu,"grades":grades}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", required=True, help='Comma-separated claims, e.g. "A, B, C"')
    ap.add_argument("--email", default="csvpreview@example.com")
    ap.add_argument("--no-test-mode", action="store_true")
    args = ap.parse_args()

    claims = _split_claims(args.claims)
    if not claims:
        sys.exit("No claims after parsing. Provide non-empty comma-separated claims.")

    token = register(args.email)
    outdir = pathlib.Path("outputs") / ("batch_" + datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S"))
    outdir.mkdir(parents=True, exist_ok=True)

    rows = []
    for i, text in enumerate(claims, 1):
        data = preview(token, text, (not args.no_test_mode))
        # Save full JSON
        (outdir / f"claim_{i:03d}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        overall = data.get("overall", {}) or {}
        claims_list = data.get("claims", []) or []
        evid = _evidence_summary(data)
        # Per-claim: pick primary first (fallback to first)
        cl = None
        for c in claims_list:
            if str(c.get("tier","")).lower()=="primary":
                cl = c; break
        if cl is None and claims_list: cl = claims_list[0]
        cscore = (cl or {}).get("score_numeric") or (cl or {}).get("score") or ""
        clabel = (cl or {}).get("label") or ""
        # Table row: # | claim | overall_score | overall_label | claim_score | claim_label | ev(s/r/n) | grades(A..F)
        rows.append((
            i,
            text[:60].replace("\n"," ") + ("..." if len(text)>60 else ""),
            overall.get("score",""),
            overall.get("label",""),
            cscore,
            clabel,
            f"{evid['support']}/{evid['refute']}/{evid['neutral']}",
            ",".join(f"{k}:{v}" for k,v in sorted(evid["grades"].items()))
        ))

    # Print compact table
    # Columns:
    # # | claim | overall_score | overall_label | claim_score | claim_label | ev(s/r/n) | grades
    colw = [4, 64, 15, 14, 12, 14, 12, 20]
    headers = ["#", "claim", "overall_score", "overall_label", "claim_score", "claim_label", "ev s/r/n", "grades"]
    def fmt_row(vals):
        return "".join(str(vals[j]).ljust(colw[j]) for j in range(len(vals)))
    print(fmt_row(headers))
    print("-" * sum(colw))
    for r in rows:
        print(fmt_row(r))
    print(f"\nSaved full results -> {outdir}/")

if __name__ == "__main__":
    main()