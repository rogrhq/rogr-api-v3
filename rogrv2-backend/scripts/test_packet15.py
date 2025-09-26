#!/usr/bin/env python3
import json, sys, time, urllib.request

BASE = "http://localhost:8000"

def post(path, data, bearer=None, timeout=45):
    url = f"{BASE}{path}"
    headers = {"Content-Type":"application/json"}
    if bearer: headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def get(path, bearer=None, timeout=45):
    url = f"{BASE}{path}"
    headers = {}
    if bearer: headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def main():
    code, reg = post("/auth/register", {"email":"packet15@example.com"})
    assert code == 200 and "access_token" in reg, f"register failed: {code} {reg}"
    tok = reg["access_token"]

    code, pv = post("/mobile/preview", {"text":"Austin increased its 2024 city budget by 8%.", "test_mode": True}, bearer=tok)
    assert code == 200, f"mobile/preview {code}"
    assert "claims" in pv and isinstance(pv["claims"], list) and pv["claims"], "preview claims missing"
    c0 = pv["claims"][0]
    for k in ("text","tier","score_numeric","label"):
        assert k in c0, f"claim missing {k}"
    assert "overall" in pv and "score" in pv["overall"] and "label" in pv["overall"], "overall missing"
    assert "methodology" in pv and "version" in pv["methodology"], "methodology missing"

    code, cm = post("/mobile/commit", {"text":"Austin increased its 2024 city budget by 8%.", "test_mode": True}, bearer=tok)
    assert code == 200 and "analysis_id" in cm, f"mobile/commit {code} {cm}"

    code, f1 = get("/mobile/feed?limit=1", bearer=tok)
    assert code == 200 and "items" in f1 and isinstance(f1["items"], list), "mobile/feed bad shape"
    assert len(f1["items"]) >= 1, "mobile/feed empty"

    code, ar = get("/mobile/archive/search?q=budget", bearer=tok)
    assert code == 200 and "results" in ar and isinstance(ar["results"], list), "mobile/archive/search bad shape"

    code, enq = post("/jobs/enqueue", {"kind":"preview","payload":{"text":"Austin increased its 2024 city budget by 8%.","test_mode": True}}, bearer=tok)
    assert code == 200 and "job_id" in enq, f"enqueue failed: {code} {enq}"
    jid = enq["job_id"]

    snap = {}
    for _ in range(40):
        code, snap = get(f"/mobile/jobs/{jid}", bearer=tok)
        assert code == 200, f"mobile/jobs status {code}"
        if snap.get("status") in ("completed","failed"):
            break
        time.sleep(0.2)
    assert snap.get("status") == "completed", f"job not completed: {snap}"
    r = snap.get("result", {})
    assert "overall" in r and "score" in r["overall"], "job result overall missing"

    print("PASS")

if __name__ == "__main__":
    main()