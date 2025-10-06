#!/usr/bin/env python3
"""
P27 (LIVE) — Deterministic Consensus over Dual Researchers

Asserts (live):
- P27 wrapper installs and rebinds preview.
- /analyses/preview returns claims[0].researchers with exactly 2 lanes (R1,R2).
- A `consensus` object is attached with {label, confidence, rationale, agreement}.
- If R1.label == R2.label -> consensus.label equals that label AND consensus.confidence >= max(c1,c2).
- If labels differ -> consensus.confidence <= max(c1,c2) (penalty applied).
"""
import json
import os
import sys
from importlib import import_module

os.environ.setdefault("ROGR_DIAG", "1")

# repo root on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Force wrapper imports order
for modname in (
    "intelligence.content.p22_ingest",
    "intelligence.content.p23_semantic",
    "intelligence.content.p24_semantic_frames",
    "intelligence.content.p25_semantic_aggregate",
    "intelligence.content.p26_dual_researchers",
    "intelligence.content.p27_consensus",
):
    try:
        import_module(modname)
    except Exception as e:
        print(f"P27 FAIL: import {modname}: {e}", file=sys.stderr); sys.exit(1)

# App
try:
    main = import_module("main")
except Exception as e:
    print(f"P27 FAIL: cannot import main: {e}", file=sys.stderr); sys.exit(1)
app = getattr(main, "app", None)
if app is None:
    print("P27 FAIL: FastAPI app not found at main.app", file=sys.stderr); sys.exit(1)

from fastapi.testclient import TestClient  # noqa
client = TestClient(app)

def _register(email: str) -> str:
    r = client.post("/auth/register", json={"email": email})
    if r.status_code != 200:
        print(f"P27 FAIL: register failed {r.status_code} {r.text}", file=sys.stderr); sys.exit(1)
    tok = r.json().get("access_token")
    if not tok:
        print("P27 FAIL: no access_token", file=sys.stderr); sys.exit(1)
    return tok

def _preview(claim: str, tok: str):
    r = client.post("/analyses/preview", json={"text": claim, "mode": "live"}, headers={"Authorization": f"Bearer {tok}"}, timeout=150)
    if r.status_code != 200:
        print(f"P27 FAIL: preview failed {r.status_code} {r.text}", file=sys.stderr); sys.exit(1)
    return r.json()

def _ok_conf(x):
    try:
        f = float(x); return 0.0 <= f <= 1.0
    except Exception:
        return False

def main():
    claim = "Austin increased its 2024 city budget by 8%"
    tok = _register("p27.consensus@test.example.com")
    j = _preview(claim, tok)

    claims = j.get("claims") or []
    if not claims:
        print("P27 FAIL: preview returned no claims", file=sys.stderr); sys.exit(1)
    c0 = claims[0]

    # lanes present
    researchers = c0.get("researchers") or []
    if len(researchers) != 2:
        print(f"P27 FAIL: expected 2 researchers, got {len(researchers)}", file=sys.stderr); sys.exit(1)

    # consensus present
    cons = c0.get("consensus") or {}
    if cons.get("label") not in {"supports","challenges","mixed","insufficient"}:
        print(f"P27 FAIL: invalid consensus label: {cons}", file=sys.stderr); sys.exit(1)
    if not _ok_conf(cons.get("confidence")):
        print(f"P27 FAIL: invalid consensus confidence: {cons}", file=sys.stderr); sys.exit(1)

    agr = cons.get("agreement") or {}
    if not {"r1_label","r2_label","r1_conf","r2_conf","delta_balance"}.issubset(agr.keys()):
        print(f"P27 FAIL: missing agreement fields: {agr}", file=sys.stderr); sys.exit(1)
    rat = cons.get("rationale") or {}
    if "rule" not in rat:
        print(f"P27 FAIL: missing rationale.rule", file=sys.stderr); sys.exit(1)

    # invariants based on agreement/disagreement
    r1v = (researchers[0].get("verdict") or {})
    r2v = (researchers[1].get("verdict") or {})
    l1, c1 = r1v.get("label"), float(r1v.get("confidence") or 0.0)
    l2, c2 = r2v.get("label"), float(r2v.get("confidence") or 0.0)
    c_conf = float(cons.get("confidence") or 0.0)

    if l1 == l2:
        if cons.get("label") != l1:
            print(f"P27 FAIL: consensus label not matching agreeing lanes: {l1} vs {cons.get('label')}", file=sys.stderr); sys.exit(1)
        if c_conf + 1e-9 < max(c1, c2):
            print(f"P27 FAIL: consensus confidence should be >= max lane conf on agreement (c={c_conf} lanes={c1},{c2})", file=sys.stderr); sys.exit(1)
    else:
        if c_conf - 1e-9 > max(c1, c2):
            print(f"P27 FAIL: consensus confidence should be <= max lane conf on disagreement (c={c_conf} lanes={c1},{c2})", file=sys.stderr); sys.exit(1)

    print(json.dumps({
        "event":"p27.test_summary",
        "consensus": {"label": cons.get("label"), "confidence": c_conf},
        "lanes": [
            {"id": researchers[0].get("id"), "label": l1, "confidence": c1},
            {"id": researchers[1].get("id"), "label": l2, "confidence": c2},
        ],
        "rule": rat.get("rule")
    }, ensure_ascii=False))
    print("PACKET PASS P27")

if __name__ == "__main__":
    main()
