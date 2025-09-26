#!/usr/bin/env python3
import json, sys, urllib.request

BASE = "http://localhost:8000"

def _req(method, path, data=None, bearer=None, timeout=60):
    url = f"{BASE}{path}"
    headers = {}
    if bearer: headers["Authorization"] = f"Bearer {bearer}"
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def post(path, data=None, **kw): return _req("POST", path, data=data, **kw)
def get(path, **kw): return _req("GET", path, **kw)

def main():
    # User registers and commits one analysis
    c, reg = post("/auth/register", {"email":"packet23@example.com"}); assert c==200; user_tok = reg["access_token"]
    c, cm = post("/mobile/commit", {"text":"Austin increased its 2024 city budget by 8%.", "test_mode": True}, bearer=user_tok); assert c==200
    aid = cm["analysis_id"]

    # user status (not frozen)
    c, me = get("/auth/me", bearer=user_tok); assert c==200 and me.get("frozen") is False

    # Elevate same user to admin (test-only)
    c, elev = post("/auth/elevate", {}, bearer=user_tok); assert c==200 and "access_token" in elev
    admin_tok = elev["access_token"]

    # Admin list analyses includes our analysis
    c, lst = get("/admin/analyses?limit=10", bearer=admin_tok); assert c==200
    ids = [it["id"] for it in lst.get("items",[])]
    assert aid in ids, f"analysis {aid} not in admin list {ids}"

    # Admin IFCN export for that analysis
    c, exp = get(f"/admin/ifcn/analyses/{aid}", bearer=admin_tok); assert c==200
    for k in ("schema_version","input","claims","overall","methodology","evidence_ledger","checksum"):
        assert k in exp, f"export missing {k}"

    # Admin audit events list (may be empty but must exist)
    c, aud = get(f"/admin/audit/analyses/{aid}", bearer=admin_tok); assert c==200
    assert "items" in aud and isinstance(aud["items"], list)

    # Freeze and check /auth/me reflects it
    c, fr = post("/admin/users/freeze", {"sub": me["sub"], "frozen": True}, bearer=admin_tok); assert c==200 and fr["frozen"] is True
    c, me2 = get("/auth/me", bearer=user_tok); assert c==200 and me2.get("frozen") is True

    # Unfreeze
    c, uf = post("/admin/users/freeze", {"sub": me["sub"], "frozen": False}, bearer=admin_tok); assert c==200 and uf["frozen"] is False
    c, me3 = get("/auth/me", bearer=user_tok); assert c==200 and me3.get("frozen") is False

    print("PASS")

if __name__ == "__main__":
    main()