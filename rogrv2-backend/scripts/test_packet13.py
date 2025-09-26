#!/usr/bin/env python3
import json, sys, urllib.request

ORIGIN = "http://localhost:19006"  # Expo default; works with CORS '*'

def post(url, data, bearer=None, timeout=30):
    headers = {"Content-Type":"application/json", "Origin": ORIGIN}
    if bearer: headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8")), dict(resp.getheaders())

def get(url, bearer=None, timeout=30):
    headers = {"Origin": ORIGIN}
    if bearer: headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8")), dict(resp.getheaders())

def main():
    # 1) auth
    code, reg, hdrs = post("http://localhost:8000/auth/register", {"email":"packet13@example.com"})
    assert code == 200 and "access_token" in reg, f"register failed: {code} {reg}"
    tok = reg["access_token"]
    # CORS header present
    assert "Access-Control-Allow-Origin" in hdrs, "CORS header missing on POST /auth/register"

    # 2) contracts endpoint
    code, body, hdrs = get("http://localhost:8000/contracts/v1/auth_me.json", bearer=tok)
    assert code == 200, f"/contracts/v1/auth_me.json {code}"
    # Has expected keys (values may differ)
    for k in ("sub","roles","exp"):
        assert k in body, f"contract body missing {k}"
    # CORS header present
    assert "Access-Control-Allow-Origin" in hdrs, "CORS header missing on GET /contracts/v1/auth_me.json"

    # 3) feed contract
    code, body, hdrs = get("http://localhost:8000/contracts/v1/feed.json", bearer=tok)
    assert code == 200 and "items" in body, "feed contract not served correctly"
    assert "Access-Control-Allow-Origin" in hdrs, "CORS header missing on feed contract"

    print("PASS")

if __name__ == "__main__":
    main()