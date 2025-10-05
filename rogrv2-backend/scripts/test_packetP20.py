#!/usr/bin/env python3
"""
P20 (LIVE) — Deterministic reading & grading test.

Ensures P20 wrapper is installed BEFORE importing the app, so findings are attached.
Asserts that for at least one content-bearing evidence item, grading fields exist:
  - item.grade (float 0..10)
  - item.stance (string)
  - item.finding: { grade, stance, matched_spans[], rationale[] }
"""
import os, sys, importlib
from typing import Any, Dict, List
from pathlib import Path

os.environ.setdefault("PYTHONUNBUFFERED", "1")

def fail(msg: str) -> None:
    print(f"P20 FAIL: {msg}")
    sys.exit(1)

def ok(msg: str) -> None:
    print(msg)

def _ensure_root_on_path():
    here = Path(__file__).resolve()
    root = here.parent.parent
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root_str

def load_app():
    _ensure_root_on_path()
    # --- FORCE EARLY WRAPPER INSTALL ---
    # sitecustomize auto-load (harmless if already loaded)
    try:
        import sitecustomize  # noqa: F401
    except Exception:
        pass
    # Explicitly import wrappers to ensure installation before app import.
    try:
        from intelligence.gather import p19_wrapper  # noqa: F401
    except Exception:
        pass
    try:
        from intelligence.content import p20_wrapper  # noqa: F401
    except Exception:
        pass
    # -----------------------------------
    m = importlib.import_module("main")
    app = getattr(m, "app", None)
    if app is None:
        fail("Cannot locate FastAPI app as main.app")
    return app

def client():
    from fastapi.testclient import TestClient
    return TestClient(load_app())

def register(cli):
    r = cli.post("/auth/register", json={"email":"p20.grading@test.example"})
    if r.status_code != 200:
        fail(f"register failed: {r.status_code} {r.text}")
    tok = (r.json() or {}).get("access_token")
    if not tok:
        fail("no access_token from /auth/register")
    return tok

def _has_finding_fields(item: Dict[str, Any]) -> bool:
    if "grade" not in item or "stance" not in item or "finding" not in item:
        return False
    f = item["finding"] or {}
    if not isinstance(f.get("grade", None), (int, float)):
        return False
    if not isinstance(f.get("stance",""), str):
        return False
    if not isinstance(f.get("matched_spans", []), list):
        return False
    if not isinstance(f.get("rationale", []), list):
        return False
    return True

def main():
    cli = client()
    tok = register(cli)
    claim = "Austin increased its 2024 city budget by 8%."
    payload = {"text": claim, "mode": "live", "max_per_arm": 2}
    r = cli.post("/analyses/preview", json=payload, headers={"Authorization": f"Bearer {tok}"})
    if r.status_code != 200:
        fail(f"/analyses/preview failed: {r.status_code} {r.text}")
    j = r.json() or {}
    claims = (j.get("claims") or [])
    if not claims:
        fail("no claims in response")
    ev = (claims[0].get("evidence") or {})
    armA = ev.get("arm_A") or []
    armB = ev.get("arm_B") or []

    # Consider only items that actually fetched content
    candA = [x for x in armA if int(x.get("content_chars") or 0) > 0]
    candB = [x for x in armB if int(x.get("content_chars") or 0) > 0]

    if not candA and not candB:
        fail("no evidence items with fetched content for grading")

    graded = 0
    for it in candA + candB:
        if _has_finding_fields(it):
            graded += 1

    if graded == 0:
        fail("no graded findings found on content-bearing items")

    ok(f"P20 PASS: {graded} graded finding(s) present")
    print("PACKET PASS P20")

if __name__ == "__main__":
    main()
