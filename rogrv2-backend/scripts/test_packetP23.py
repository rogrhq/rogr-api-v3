#!/usr/bin/env python3
"""
P23 test (LIVE): deterministic semantic reading attaches findings & item grades.
Checks (with ROGR_DIAG=1):
- sitecustomize + p22 + p23 modules import
- preview (canonical shape) succeeds
- each arm has >=1 item with findings[] length >=1
- each finding has quote, offsets (int), stance, score in [0,1]
- each item has item_grade (0..1) and grade_label
No API shape changes asserted.
"""
import json
import os
import sys
from importlib import import_module
from typing import Any, Dict, List

os.environ.setdefault("ROGR_DIAG", "1")

# sys.path: ensure repo root present
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Import activation BEFORE app
try:
    import sitecustomize  # noqa: F401
except Exception as e:
    print(f"P23 FAIL: sitecustomize import error: {e}", file=sys.stderr); sys.exit(1)
try:
    import intelligence.content.p22_ingest  # noqa: F401
    import intelligence.content.p23_semantic  # noqa: F401
except Exception as e:
    print(f"P23 FAIL: p22/p23 import error: {e}", file=sys.stderr); sys.exit(1)

# Import app
try:
    main = import_module("main")
except Exception as e:
    print(f"P23 FAIL: cannot import main: {e}", file=sys.stderr); sys.exit(1)
app = getattr(main, "app", None)
if app is None:
    print("P23 FAIL: FastAPI app not found at main.app", file=sys.stderr); sys.exit(1)

from fastapi.testclient import TestClient  # noqa: E402
client = TestClient(app)

def _register_token(email: str) -> str:
    r = client.post("/auth/register", json={"email": email})
    if r.status_code != 200:
        print(f"P23 FAIL: register failed {r.status_code} {r.text}", file=sys.stderr); sys.exit(1)
    tok = r.json().get("access_token")
    if not tok:
        print("P23 FAIL: no access_token", file=sys.stderr); sys.exit(1)
    return tok

def _preview(claim: str, token: str) -> Dict[str, Any]:
    r = client.post("/analyses/preview", json={"text": claim, "mode": "live"}, headers={"Authorization": f"Bearer {token}"}, timeout=60)
    if r.status_code != 200:
        print(f"P23 FAIL: preview failed {r.status_code} {r.text}", file=sys.stderr); sys.exit(1)
    return r.json()

def _iter_items(resp: Dict[str, Any], arm: str) -> List[Dict[str,Any]]:
    claims = resp.get("claims") or []
    if not claims or not isinstance(claims[0], dict):
        return []
    ev = claims[0].get("evidence") or {}
    return ev.get(arm) or []

def _check_findings(items: List[Dict[str,Any]], arm_name: str) -> None:
    # require at least 1 item with >=1 finding
    found_any = False
    for it in items:
        findings = it.get("findings") or []
        if findings:
            found_any = True
            for fd in findings[:3]:
                quote = fd.get("quote"); stance = fd.get("stance"); sc = fd.get("score")
                os_ = fd.get("offset_start"); oe_ = fd.get("offset_end")
                if not isinstance(quote, str) or not quote:
                    print(f"P23 FAIL: missing quote in {arm_name}", file=sys.stderr); sys.exit(1)
                if not isinstance(os_, int) or not isinstance(oe_, int):
                    print(f"P23 FAIL: missing offsets in {arm_name}", file=sys.stderr); sys.exit(1)
                if stance not in ("support","challenge","mixed","unrelated"):
                    print(f"P23 FAIL: invalid stance in {arm_name}", file=sys.stderr); sys.exit(1)
                if not (isinstance(sc, (int,float)) and 0.0 <= sc <= 1.0):
                    print(f"P23 FAIL: invalid score in {arm_name}", file=sys.stderr); sys.exit(1)
        # item grade checks
        ig = it.get("item_grade"); gl = it.get("grade_label")
        if not (isinstance(ig, (int,float)) and 0.0 <= ig <= 1.0):
            print(f"P23 FAIL: missing/invalid item_grade in {arm_name}", file=sys.stderr); sys.exit(1)
        if gl not in ("high","medium","low"):
            print(f"P23 FAIL: missing/invalid grade_label in {arm_name}", file=sys.stderr); sys.exit(1)

    if not found_any:
        print(f"P23 FAIL: no findings produced on {arm_name}", file=sys.stderr); sys.exit(1)

def main():
    claim = "Austin increased its 2024 city budget by 8%"
    token = _register_token("p23.semantic@test.example.com")
    resp = _preview(claim, token)

    a_items = _iter_items(resp, "arm_A")
    b_items = _iter_items(resp, "arm_B")
    print(json.dumps({"event":"p23.test_items","A":len(a_items),"B":len(b_items)}, ensure_ascii=False))

    if len(a_items) == 0 or len(b_items) == 0:
        print("P23 FAIL: no items on one of the arms", file=sys.stderr); sys.exit(1)

    _check_findings(a_items, "arm_A")
    _check_findings(b_items, "arm_B")
    print("PACKET PASS P23")

if __name__ == "__main__":
    main()
