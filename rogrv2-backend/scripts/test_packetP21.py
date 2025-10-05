#!/usr/bin/env python3
"""
P21 LIVE test: ensures full-read fields are attached to at least one item.
- Imports p20 and p21 wrappers BEFORE app import to guarantee installation.
- Calls /auth/register and /analyses/preview (live).
- Verifies at least one item has: grade_full (0..10), stance_full, credibility ∈ [0,1].
"""

import os, sys, json, importlib
from typing import Any, Dict, List
from pathlib import Path

os.environ.setdefault("PYTHONUNBUFFERED", "1")
os.environ.setdefault("ROGR_DIAG_P21", "1")

def _ensure_root_on_path() -> str:
    here = Path(__file__).resolve()
    root = here.parent.parent
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root_str

def _load_app():
    _ensure_root_on_path()
    # Force wrappers before app import
    try:
        import sitecustomize  # noqa
    except Exception:
        pass
    for mod in ("intelligence.content.p20_wrapper",
                "intelligence.content.p21_wrapper"):
        try:
            importlib.import_module(mod)
        except Exception as e:
            print(json.dumps({"event":"p21.import_error","module":mod,"error":str(e)}))
    m = importlib.import_module("main")
    app = getattr(m, "app", None)
    if app is None:
        raise RuntimeError("Cannot locate FastAPI app at main.app")
    return app

def _client(app):
    from fastapi.testclient import TestClient
    return TestClient(app)

def _get_token(client) -> str:
    r = client.post("/auth/register", json={"email": "p21.tester@example.com"})
    if r.status_code != 200:
        raise RuntimeError(f"register failed: {r.status_code} {r.text}")
    j = r.json()
    return j.get("access_token") or j.get("token") or ""

def _flatten_items_from_response(j: Dict[str, Any]) -> List[Dict[str,Any]]:
    # Prefer nested claim evidence
    claims = j.get("claims") or []
    if isinstance(claims, list) and claims:
        ev = (claims[0] or {}).get("evidence") or {}
    else:
        ev = j.get("evidence") or {}
    out: List[Dict[str,Any]] = []
    for key in ("arm_A","A","arm_B","B"):
        if key not in ev:
            continue
        val = ev.get(key)
        if isinstance(val, list):
            out.extend(val)
        elif isinstance(val, dict):
            if isinstance(val.get("candidates"), list):
                out.extend(val["candidates"])
            else:
                for _, v in val.items():
                    if isinstance(v, list):
                        out.extend(v)
    return out

def _preview(client, token: str) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    claim = "Austin increased its 2024 city budget by 8%."
    # Try common body shapes used in repo
    bodies = [
        {"text": claim, "live": True},
        {"input": claim, "live": True},
        {"claims": [{"text": claim}], "live": True},
    ]
    last = None
    for body in bodies:
        r = client.post("/analyses/preview", json=body, headers=headers)
        last = r
        if r.status_code == 200:
            return r.json()
    raise RuntimeError(f"preview failed: {last.status_code} {last.text if last is not None else ''}")

def main() -> None:
    app = _load_app()
    client = _client(app)
    token = _get_token(client)
    j = _preview(client, token)
    items = _flatten_items_from_response(j)

    if not items:
        raise AssertionError("P21 FAIL: no evidence items returned")

    def _ok(it: Dict[str,Any]) -> bool:
        gf = it.get("grade_full")
        sf = it.get("stance_full")
        cr = it.get("credibility")
        if not isinstance(gf, (int, float)): return False
        if not isinstance(sf, str): return False
        if not isinstance(cr, (int, float)): return False
        return 0.0 <= float(gf) <= 10.0 and 0.0 <= float(cr) <= 1.0 and sf in {"support","challenge","mixed","unrelated"}

    matched = [it for it in items if _ok(it)]
    print(f"P21 items total={len(items)} matched={len(matched)}")
    if not matched:
        # print a small diagnostic sample
        for it in items[:3]:
            print(json.dumps({k: it.get(k) for k in ("title","grade_full","stance_full","credibility")}, ensure_ascii=False))
        raise AssertionError("P21 FAIL: no items with full-read fields")
    print("PACKET PASS P21")

if __name__ == "__main__":
    main()
