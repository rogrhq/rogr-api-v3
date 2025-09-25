#!/usr/bin/env python3
import json, sys, urllib.request

def post(url, data, bearer=None):
    headers = {"Content-Type":"application/json"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        return resp.getcode(), json.loads(body)

def main():
    # 1) Register to get JWT
    code, reg = post("http://localhost:8000/auth/register", {"email":"packet8-offline@example.com"})
    assert code == 200 and "access_token" in reg, f"register failed: {code} {reg}"
    tok = reg["access_token"]

    # 2) Offline branch should always work without API keys
    status, body = post("http://localhost:8000/analyses/preview",
                        {"text":"Austin increased its 2024 city budget by 8%.", "test_mode": True},
                        bearer=tok)
    assert status == 200, f"Expected 200, got {status}"
    assert "claims" in body and isinstance(body["claims"], list), "Body missing 'claims' list"
    print("PASS: Packet 8 offline branch OK")
if __name__ == "__main__":
    main()