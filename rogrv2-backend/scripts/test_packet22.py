#!/usr/bin/env python3
import json, sys, time, urllib.request

BASE = "http://localhost:8000"

def _req(method, path, data=None, bearer=None, timeout=60, headers=None):
    url = f"{BASE}{path}"
    hdrs = {} if headers is None else dict(headers)
    if bearer: hdrs["Authorization"] = f"Bearer {bearer}"
    if data is not None:
        hdrs["Content-Type"] = "application/json"
        data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return resp.getcode(), json.loads(body)

def post(path, data=None, **kw): return _req("POST", path, data=data, **kw)
def get(path, **kw): return _req("GET", path, **kw)

def main():
    # Register two users
    c, a = post("/auth/register", {"email":"notify_u1@example.com"}); assert c==200; tok1 = a["access_token"]
    c, b = post("/auth/register", {"email":"notify_u2@example.com"}); assert c==200; tok2 = b["access_token"]

    # u1 follows u2 -> u2 should receive a "follow" notification
    c, _ = post("/profile/handle", {"handle":"nu1"}, bearer=tok1); assert c==200
    c, _ = post("/profile/handle", {"handle":"nu2"}, bearer=tok2); assert c==200
    c, _ = post("/profile/follow", {"target":"nu2","kind":"handle"}, bearer=tok1); assert c==200

    # fetch notifications as u2
    c, n2 = get("/notifications?unread_only=true", bearer=tok2); assert c==200
    items = n2.get("items", [])
    assert any(it.get("kind")=="follow" for it in items), f"follow notification missing: {items}"

    # u1 enqueues a job and polls until completed, then should see a job_completed notification
    c, enq = post("/jobs/enqueue", {"kind":"preview","payload":{"text":"Austin increased its 2024 city budget by 8%.","test_mode": True}}, bearer=tok1); assert c==200
    jid = enq["job_id"]

    # poll job status via mobile path to trigger notification emission
    status = ""
    for _ in range(50):
        time.sleep(0.2)
        c, js = get(f"/mobile/jobs/{jid}", bearer=tok1); assert c==200
        status = js.get("status","")
        if status in ("completed","failed"):
            break
    assert status == "completed", f"job did not complete: {status}"

    # fetch notifications as u1; look for job_* with this job_id
    c, n1 = get("/notifications?unread_only=false", bearer=tok1); assert c==200
    items = n1.get("items", [])
    assert any(it.get("kind") in ("job_completed","job_failed") and it.get("payload",{}).get("job_id")==jid for it in items), f"job notification missing for {jid}: {items}"

    # ack all notifications for u1
    ids = [it["id"] for it in items]
    if ids:
        c, ack = post("/notifications/ack", {"ids": ids}, bearer=tok1); assert c==200 and "updated" in ack

    print("PASS")

if __name__ == "__main__":
    main()