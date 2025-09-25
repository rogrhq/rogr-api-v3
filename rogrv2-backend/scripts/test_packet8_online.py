#!/usr/bin/env python3
import os, json, sys, urllib.request
def post(url, data, bearer=None):
    headers = {"Content-Type":"application/json"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8")
        return resp.getcode(), json.loads(body)
def main():
    # Only run if at least one provider is configured
    if not ((os.getenv("GOOGLE_CSE_API_KEY") and os.getenv("GOOGLE_CSE_ENGINE_ID")) or os.getenv("BING_API_KEY")):
        print("SKIP: API keys not present; online test skipped")
        return
    # Register to get JWT
    code, reg = post("http://localhost:8000/auth/register", {"email":"packet8-online@example.com"})
    assert code == 200 and "access_token" in reg, f"register failed: {code} {reg}"
    tok = reg["access_token"]
    status, body = post("http://localhost:8000/analyses/preview",
                        {"text":"Austin 2024 city budget increase", "test_mode": False},
                        bearer=tok)
    assert status == 200, f"Expected 200, got {status}"
    # Expect at least one evidence item referencing a snapshot path when providers return results
    claims = body.get("claims", [])
    assert claims, "No claims returned"
    any_snap = False
    for c in claims:
        for arm in ("A","B"):
            for ev in c.get("evidence",{}).get(arm,[]):
                src = ev.get("source", {})
                if isinstance(src, dict) and isinstance(src.get("snapshot"), dict) and src["snapshot"].get("path"):
                    any_snap = True
                    break
    assert any_snap, "Expected at least one snapshot path in sources"
    print("PASS: Packet 8 online branch OK")
if __name__ == "__main__":
    main()