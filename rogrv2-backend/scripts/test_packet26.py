#!/usr/bin/env python3
import json, sys, urllib.request

BASE = "http://localhost:8000"

def get(path, timeout=40):
    url = f"{BASE}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def main():
    # Contracts index
    c, idx = get("/contracts/v2"); assert c==200
    items = idx.get("items", [])
    want = {"analyses_preview","mobile_commit","media_upload","notifications_list","feed_get"}
    assert want.issubset(set(items)), f"contracts missing: {want - set(items)}"

    # Fetch a couple of contracts
    for name in ["analyses_preview","media_upload"]:
        c, doc = get(f"/contracts/v2/{name}"); assert c==200
        assert "request" in doc and "response" in doc, f"contract {name} missing keys"

    # Postman export available
    c, pm = get("/contracts/v2/postman"); assert c==200 and "item" in pm

    # OpenAPI examples present (check schemas for request bodies we patched)
    c, oa = get("/openapi.json"); assert c==200
    comps = oa.get("components", {}).get("schemas", {})
    # Either RegisterBody or PreviewFromMediaBody must expose examples
    rb = comps.get("RegisterBody", {})
    pvb = comps.get("PreviewFromMediaBody", {})
    ok = ("examples" in rb) or ("examples" in pvb)
    assert ok, "OpenAPI schemas missing examples for request models"

    print("PASS")

if __name__ == "__main__":
    main()