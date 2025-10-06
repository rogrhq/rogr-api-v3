#!/usr/bin/env python3
"""
P24 (LIVE) — Deterministic semantic frames & entailment test.
Asserts:
- p24 wrapper installs and rebinds preview
- Live preview returns claims with evidence
- Each arm has items; for arms with content/excerpt present, at least one item exposes:
  * item_frame (dict with keys)
  * frame_matches (list) where at least one match has label in {entail, contradict, mixed, unrelated}
  * frame_confidence float in [0,1]
We also require at least ONE frame match overall (across both arms) to avoid trivial passes.
No API shape changes are assumed/required.
"""
import json
import os
import sys
from importlib import import_module
from typing import Any, Dict, List

os.environ.setdefault("ROGR_DIAG", "1")

# Ensure repo on path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Activation before app import
try:
    import sitecustomize  # noqa
except Exception as e:
    print(f"P24 FAIL: sitecustomize import error: {e}", file=sys.stderr); sys.exit(1)

# Import P22/P23/P24 to ensure install order
for modname in ("intelligence.content.p22_ingest","intelligence.content.p23_semantic","intelligence.content.p24_semantic_frames"):
    try:
        import_module(modname)
    except Exception as e:
        print(f"P24 FAIL: import {modname}: {e}", file=sys.stderr); sys.exit(1)

# App import
try:
    main = import_module("main")
except Exception as e:
    print(f"P24 FAIL: cannot import main: {e}", file=sys.stderr); sys.exit(1)
app = getattr(main, "app", None)
if app is None:
    print("P24 FAIL: FastAPI app not found at main.app", file=sys.stderr); sys.exit(1)

from fastapi.testclient import TestClient  # noqa
client = TestClient(app)

def _register(email: str) -> str:
    r = client.post("/auth/register", json={"email": email})
    if r.status_code != 200:
        print(f"P24 FAIL: register failed {r.status_code} {r.text}", file=sys.stderr); sys.exit(1)
    tok = r.json().get("access_token")
    if not tok:
        print("P24 FAIL: no access_token", file=sys.stderr); sys.exit(1)
    return tok

def _preview(claim: str, tok: str) -> Dict[str,Any]:
    r = client.post("/analyses/preview", json={"text": claim, "mode": "live"}, headers={"Authorization": f"Bearer {tok}"}, timeout=75)
    if r.status_code != 200:
        print(f"P24 FAIL: preview failed {r.status_code} {r.text}", file=sys.stderr); sys.exit(1)
    return r.json()

def _items(resp: Dict[str,Any], arm: str) -> List[Dict[str,Any]]:
    claims = resp.get("claims") or []
    if not claims: return []
    ev = claims[0].get("evidence") or {}
    return ev.get(arm) or []

def _has_content_like(it: Dict[str,Any]) -> bool:
    return bool(it.get("content") or it.get("content_excerpt"))

def _check_arm(arm_items: List[Dict[str,Any]], arm_name: str) -> Dict[str,int]:
    # returns counts for diagnostics
    has_frame = 0
    has_match = 0
    for it in arm_items:
        if "item_frame" in it and isinstance(it.get("item_frame"), dict):
            fconf = it.get("frame_confidence")
            if isinstance(fconf, (int,float)) and 0.0 <= fconf <= 1.0:
                has_frame += 1
        matches = it.get("frame_matches") or []
        for m in matches:
            lab = m.get("label")
            sc  = m.get("score")
            q   = m.get("quote")
            os_ = m.get("offset_start"); oe_ = m.get("offset_end")
            if lab in ("entail","contradict","mixed","unrelated") and isinstance(sc,(int,float)) and 0.0 <= sc <= 1.0 and isinstance(q,str) and isinstance(os_,int) and isinstance(oe_,int):
                has_match += 1
                break
    return {"has_frame": has_frame, "has_match": has_match}

def main():
    claim = "Austin increased its 2024 city budget by 8%"
    tok = _register("p24.frames@test.example.com")
    resp = _preview(claim, tok)

    A = _items(resp, "arm_A")
    B = _items(resp, "arm_B")
    if len(A) == 0 or len(B) == 0:
        print("P24 FAIL: one arm has zero items", file=sys.stderr); sys.exit(1)

    cA = _check_arm(A, "arm_A")
    cB = _check_arm(B, "arm_B")

    # At least one match overall, and frames present on both arms (where content/excerpt exists)
    total_matches = cA["has_match"] + cB["has_match"]
    if total_matches == 0:
        print("P24 FAIL: no frame matches produced on either arm", file=sys.stderr); sys.exit(1)

    # If an arm has any content-bearing items, require at least one frame extracted
    for arm_name, items, counts in (("arm_A", A, cA), ("arm_B", B, cB)):
        if any(_has_content_like(it) for it in items):
            if counts["has_frame"] == 0:
                print(f"P24 FAIL: no item_frame on {arm_name} despite content", file=sys.stderr); sys.exit(1)

    print(json.dumps({"event":"p24.test_summary","A":cA,"B":cB}, ensure_ascii=False))
    print("PACKET PASS P24")

if __name__ == "__main__":
    main()
