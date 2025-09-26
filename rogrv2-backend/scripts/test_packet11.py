#!/usr/bin/env python3
import json, sys, urllib.request

def post(url, data, bearer=None, timeout=30):
    headers = {"Content-Type":"application/json"}
    if bearer: headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def main():
    # 1) auth
    code, reg = post("http://localhost:8000/auth/register", {"email":"packet11@example.com"})
    assert code == 200 and "access_token" in reg, f"register failed: {code} {reg}"
    tok = reg["access_token"]

    # 2) preview (offline deterministic path)
    code, body = post("http://localhost:8000/analyses/preview", {"text":"Austin increased its 2024 city budget by 8%.", "test_mode": True}, bearer=tok)
    assert code == 200, f"preview failed: {code}"
    claims = body.get("claims", [])
    assert claims, "no claims returned"

    # 3) per-claim checks
    for c in claims:
        # Counter-claims must exist
        cc = c.get("counter_claims", [])
        assert isinstance(cc, list) and len(cc) >= 1, "missing counter_claims"
        # Evidence letters must be A..F
        for arm in ("A","B"):
            for ev in c.get("evidence",{}).get(arm,[]):
                ql = ev.get("quality_letter","")
                assert isinstance(ql, str) and len(ql) == 1 and ql.isalpha(), f"bad quality_letter: {ql!r}"
                assert ql in ("A","B","C","D","E","F"), f"quality_letter not in A..F: {ql}"

    print("PASS")

if __name__ == "__main__":
    main()