#!/usr/bin/env python3
import json, sys, time, urllib.request

BASE = "http://localhost:8000"

def _req(method, path, data=None, bearer=None, timeout=45):
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
    # Register two users
    c, a = post("/auth/register", {"email":"u1@example.com"}); assert c==200; tok1 = a["access_token"]
    c, b = post("/auth/register", {"email":"u2@example.com"}); assert c==200; tok2 = b["access_token"]

    # Set handles
    c, _ = post("/profile/handle", {"handle":"u1"}, bearer=tok1); assert c==200
    c, _ = post("/profile/handle", {"handle":"u2"}, bearer=tok2); assert c==200

    # User2 commits two analyses
    c, _ = post("/mobile/commit", {"text":"Austin increased its 2024 city budget by 8%.", "test_mode": True}, bearer=tok2); assert c==200
    c, _ = post("/mobile/commit", {"text":"Austin decreased its 2023 parks funding by 3%.", "test_mode": True}, bearer=tok2); assert c==200

    # User1 checks feed following_only before following -> expect empty or none of u2 guaranteed
    c, f0 = get("/mobile/feed?following_only=true&limit=5", bearer=tok1); assert c==200
    assert isinstance(f0.get("items",[]), list)

    # User1 follows u2
    c, _ = post("/profile/follow", {"target":"u2","kind":"handle"}, bearer=tok1); assert c==200

    # Personalized feed now should include items (>=1)
    c, f1 = get("/mobile/feed?following_only=true&limit=5", bearer=tok1); assert c==200
    assert len(f1.get("items",[])) >= 1, f"expected items in following_only feed, got {f1}"

    # Unfollow -> personalized feed likely empty again
    c, _ = post("/profile/unfollow", {"target":"u2","kind":"handle"}, bearer=tok1); assert c==200
    c, f2 = get("/mobile/feed?following_only=true&limit=5", bearer=tok1); assert c==200
    # not strictly guaranteed to be zero if other followees exist, but in test it should be zero
    assert len(f2.get("items",[])) == 0, f"expected empty after unfollow, got {f2}"

    print("PASS")

if __name__ == "__main__":
    main()