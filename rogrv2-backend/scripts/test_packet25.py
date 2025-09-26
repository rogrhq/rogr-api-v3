#!/usr/bin/env python3
import json, sys, urllib.request, time

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
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def post(path, data=None, **kw): return _req("POST", path, data=data, **kw)
def get(path, **kw): return _req("GET", path, **kw)

def main():
    # Baseline metrics
    c, m0 = get("/metrics"); assert c==200

    # Auth and a couple of API hits to move counters
    c, reg = post("/auth/register", {"email":"metrics@example.com"}); assert c==200
    tok = reg["access_token"]

    # Health ready (public) + a protected preview to generate some load
    c, rdy = get("/health/ready"); assert c==200 and rdy.get("ready") is True
    c, pv = post("/analyses/preview", {"text":"Austin increased its 2024 city budget by 8%.", "test_mode": True}, bearer=tok); assert c==200

    # Fetch metrics again
    c, m1 = get("/metrics"); assert c==200

    # Validate structure
    for k in ("requests_total","status_2xx","status_4xx","status_5xx","in_flight","request_latency_ms"):
        assert k in m1, f"metrics missing {k}"
    assert isinstance(m1["requests_total"], int)
    assert isinstance(m1["status_2xx"], int)
    assert isinstance(m1["in_flight"], int)
    assert "count" in m1["request_latency_ms"] and "sum_ms" in m1["request_latency_ms"]

    # Validate increments (requests_total should grow)
    assert m1["requests_total"] >= m0.get("requests_total", 0) + 2, f"requests_total did not increase: {m0} -> {m1}"

    print("PASS")

if __name__ == "__main__":
    main()