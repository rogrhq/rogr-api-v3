#!/usr/bin/env python3
import json, sys, time, urllib.request

def post(url, data, bearer=None, timeout=30):
    headers = {"Content-Type":"application/json"}
    if bearer: headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def get(url, bearer=None, timeout=30):
    headers = {}
    if bearer: headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def main():
    # 1) auth
    code, reg = post("http://localhost:8000/auth/register", {"email":"packet12@example.com"})
    assert code == 200 and "access_token" in reg, f"register failed: {code} {reg}"
    tok = reg["access_token"]

    # 2) enqueue preview job (offline deterministic)
    code, enq = post("http://localhost:8000/jobs/enqueue", {"kind":"preview","payload":{"text":"Austin increased its 2024 city budget by 8%.","test_mode": True}}, bearer=tok)
    assert code == 200 and "job_id" in enq, f"enqueue failed: {code} {enq}"
    jid = enq["job_id"]

    # 3) poll until completed
    for _ in range(40):  # up to ~8s
        code, snap = get(f"http://localhost:8000/jobs/{jid}", bearer=tok)
        assert code == 200, f"status fetch failed: {code}"
        if snap.get("status") in ("completed","failed"):
            break
        time.sleep(0.2)

    assert snap.get("status") == "completed", f"job did not complete: {snap}"
    # Minimal shape checks
    res = snap.get("result", {})
    assert "counts" in res and res["counts"].get("claims", 0) >= 1, "result missing counts"
    assert "overall" in res and "score" in res["overall"] and "label" in res["overall"], "result missing overall"

    print("PASS")

if __name__ == "__main__":
    main()