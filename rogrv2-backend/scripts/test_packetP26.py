#!/usr/bin/env python3
"""
P26 (LIVE) — Dual-Researcher Orchestrator test.

Asserts:
- P26 wrapper installs and rebinds preview.
- /analyses/preview (live) returns claims[0].researchers with exactly 2 lanes (R1,R2).
- Each lane has a verdict with {label, confidence} in bounds and evidence with both arms present.
- Top-level fields remain present (back-compat).
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

# Load sitecustomize (ensures earlier wrappers load)
try:
    import sitecustomize  # noqa
except Exception as e:
    print(f"P26 FAIL: sitecustomize import error: {e}", file=sys.stderr); sys.exit(1)

# Import wrappers explicitly to guarantee order
for modname in (
    "intelligence.content.p22_ingest",
    "intelligence.content.p23_semantic",
    "intelligence.content.p24_semantic_frames",
    "intelligence.content.p25_semantic_aggregate",
    "intelligence.content.p26_dual_researchers",
):
    try:
        import_module(modname)
    except Exception as e:
        print(f"P26 FAIL: import {modname}: {e}", file=sys.stderr); sys.exit(1)

# App
try:
    main = import_module("main")
except Exception as e:
    print(f"P26 FAIL: cannot import main: {e}", file=sys.stderr); sys.exit(1)
app = getattr(main, "app", None)
if app is None:
    print("P26 FAIL: FastAPI app not found at main.app", file=sys.stderr); sys.exit(1)

from fastapi.testclient import TestClient  # noqa
client = TestClient(app)

def _register(email: str) -> str:
    r = client.post("/auth/register", json={"email": email})
    if r.status_code != 200:
        print(f"P26 FAIL: register failed {r.status_code} {r.text}", file=sys.stderr); sys.exit(1)
    tok = r.json().get("access_token")
    if not tok:
        print("P26 FAIL: no access_token", file=sys.stderr); sys.exit(1)
    return tok

def _preview(claim: str, tok: str):
    r = client.post("/analyses/preview", json={"text": claim, "mode": "live"}, headers={"Authorization": f"Bearer {tok}"}, timeout=120)
    if r.status_code != 200:
        print(f"P26 FAIL: preview failed {r.status_code} {r.text}", file=sys.stderr); sys.exit(1)
    return r.json()

def _ok_conf(v): return isinstance(v, (int,float)) and 0.0 <= float(v) <= 1.0

def main():
    claim = "Austin increased its 2024 city budget by 8%"
    tok = _register("p26.dual@test.example.com")
    j = _preview(claim, tok)

    claims = j.get("claims") or []
    if not claims:
        print("P26 FAIL: preview returned no claims", file=sys.stderr); sys.exit(1)
    c0 = claims[0]

    # researchers present
    researchers = c0.get("researchers") or []
    if len(researchers) != 2:
        print(f"P26 FAIL: expected 2 researchers, got {len(researchers)}", file=sys.stderr); sys.exit(1)
    ids = {r.get("id") for r in researchers}
    if ids != {"R1","R2"}:
        print(f"P26 FAIL: researcher ids mismatch: {ids}", file=sys.stderr); sys.exit(1)

    # validate each lane
    for r in researchers:
        v = r.get("verdict") or {}
        if v.get("label") not in {"supports","challenges","mixed","insufficient"}:
            print(f"P26 FAIL: invalid lane verdict label: {v}", file=sys.stderr); sys.exit(1)
        if not _ok_conf(v.get("confidence", 0)):
            print(f"P26 FAIL: invalid lane verdict confidence: {v}", file=sys.stderr); sys.exit(1)

        ev = r.get("evidence") or {}
        A = ev.get("arm_A") or []
        B = ev.get("arm_B") or []
        if len(A) == 0 or len(B) == 0:
            print("P26 FAIL: lane evidence missing items on one arm", file=sys.stderr); sys.exit(1)

    # back-compat: top-level fields still exist
    tv = (c0.get("verdict") or {})
    if tv.get("label") not in {"supports","challenges","mixed","insufficient"}:
        print(f"P26 FAIL: missing/invalid top-level verdict: {tv}", file=sys.stderr); sys.exit(1)

    print(json.dumps({
        "event":"p26.test_summary",
        "researchers": len(researchers),
        "top_verdict": tv.get("label"),
        "lane_labels": [ (r.get("id"), (r.get("verdict") or {}).get("label")) for r in researchers ]
    }, ensure_ascii=False))
    print("PACKET PASS P26")

if __name__ == "__main__":
    main()
