#!/usr/bin/env python3
import json, sys, urllib.request

def post(url, data, bearer=None, timeout=45):
    headers = {"Content-Type":"application/json"}
    if bearer: headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def get(url, bearer=None, timeout=45):
    headers = {}
    if bearer: headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def main():
    # auth
    code, reg = post("http://localhost:8000/auth/register", {"email":"packet14@example.com"})
    assert code == 200 and "access_token" in reg, f"register failed: {code} {reg}"
    tok = reg["access_token"]

    # commit #1
    code, c1 = post("http://localhost:8000/analyses/commit", {"text":"Austin increased its 2024 city budget by 8%.", "test_mode": True}, bearer=tok)
    assert code == 200 and "analysis_id" in c1, f"commit 1 failed: {code} {c1}"

    # commit #2
    code, c2 = post("http://localhost:8000/analyses/commit", {"text":"Austin decreased its 2023 parks funding by 3%.", "test_mode": True}, bearer=tok)
    assert code == 200 and "analysis_id" in c2, f"commit 2 failed: {code} {c2}"

    # feed page 1
    code, f1 = get("http://localhost:8000/feed?limit=1", bearer=tok)
    assert code == 200 and "items" in f1, f"feed page1 failed: {code} {f1}"
    assert len(f1["items"]) == 1, "expected 1 item on page1"
    assert f1.get("next_cursor"), "expected next_cursor"

    # feed page 2
    cur = f1["next_cursor"]
    code, f2 = get(f"http://localhost:8000/feed?cursor={cur}&limit=2", bearer=tok)
    assert code == 200 and "items" in f2, f"feed page2 failed: {code} {f2}"
    assert len(f2["items"]) >= 1, "expected >=1 items on page2"

    # archive search
    code, ar = get("http://localhost:8000/archive/search?q=budget", bearer=tok)
    assert code == 200 and "results" in ar, f"archive search failed: {code} {ar}"
    assert any("budget" in (r["claims"][0]["text"].lower() if r["claims"] else "") for r in ar["results"]), "expected a result containing 'budget'"

    print("PASS")

if __name__ == "__main__":
    main()