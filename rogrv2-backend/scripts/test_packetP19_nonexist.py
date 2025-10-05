#!/usr/bin/env python3
"""
P19 STRICT (LIVE): Non-existence aware verification for arm_B.

Pass if:
  1) arm_B has at least one aligned item (matches present), OR
  2) arm_B has no aligned items BUT coverage is adequate when running the gather plan directly:
       - frames_attempted >= 3
       - providers_used  >= 2
       - queries_issued  >= 4
This test does NOT depend on API to expose extra metadata. It verifies coverage via online.run_plan().
"""
import os, sys, importlib, asyncio
from typing import Any, Dict, List
from pathlib import Path

os.environ.setdefault("PYTHONUNBUFFERED", "1")

def fail(msg: str) -> None:
    print(f"P19-NONEXIST FAIL: {msg}")
    sys.exit(1)

def ok(msg: str) -> None:
    print(msg)

def _ensure_repo_root_on_path() -> Path:
    """
    Make sure the repository root (which should contain main.py) is on sys.path.
    We assume this test lives at scripts/, so repo root is parent of this file's directory.
    If main.py is not at root, attempt to locate it and add its parent.
    """
    here = Path(__file__).resolve()
    root = here.parent.parent
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    # If main still not importable, search for a main.py and add its parent
    try:
        importlib.import_module("main")
        return root
    except Exception:
        pass
    try:
        for p in root.rglob("main.py"):
            alt = str(p.parent)
            if alt not in sys.path:
                sys.path.insert(0, alt)
            try:
                importlib.import_module("main")
                return Path(alt)
            except Exception:
                continue
    except Exception:
        # rglob failure should not crash the test; fall back to root
        return root
    return root

def load_app():
    _ensure_repo_root_on_path()
    m = importlib.import_module("main")
    app = getattr(m, "app", None)
    if app is None:
        fail("Cannot locate FastAPI app as main.app")
    return app

def client():
    from fastapi.testclient import TestClient
    return TestClient(load_app())

def register(cli):
    r = cli.post("/auth/register", json={"email":"p19.nonexist@test.example"})
    if r.status_code != 200:
        fail(f"register failed: {r.status_code} {r.text}")
    tok = (r.json() or {}).get("access_token")
    if not tok:
        fail("no access_token from /auth/register")
    return tok

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
    armB = ev.get("arm_B") or []

    # 1) Accept if arm_B aligned via API already
    if any((it.get("matches") or []) for it in armB):
        ok("P19-NONEXIST PASS: arm_B aligned")
        print("PACKET PASS P19-NONEXIST")
        return

    # 2) Otherwise, check coverage directly via gather.online.run_plan()
    try:
        from intelligence.gather import online
    except Exception as e:
        fail(f"import online failed: {e}")

    plan = {
        "claim": {"text": claim},
        "arms": [
            {"name": "A", "intent": "support", "queries": ["Austin 2024 budget increase report"]},
            {"name": "B", "intent": "challenge", "queries": ["Austin 2024 budget increase dispute"]}
        ]
    }
    res = asyncio.get_event_loop().run_until_complete(online.run_plan(plan, max_per_query=2))
    cov = (res or {}).get("coverage_by_arm") or {}
    covB = cov.get("B") or {}

    frames_attempted = int(covB.get("frames_attempted") or 0)
    providers_used = int(covB.get("providers_used") or 0)
    queries_issued = int(covB.get("queries_issued") or 0)

    if frames_attempted < 3:
        fail(f"insufficient frames_attempted: {frames_attempted} (need >=3)")
    if providers_used < 2:
        fail(f"insufficient providers_used: {providers_used} (need >=2)")
    if queries_issued < 4:
        fail(f"insufficient queries_issued: {queries_issued} (need >=4)")

    ok("P19-NONEXIST PASS: no credible counter-evidence with adequate coverage")
    print("PACKET PASS P19-NONEXIST")

if __name__ == "__main__":
    main()
