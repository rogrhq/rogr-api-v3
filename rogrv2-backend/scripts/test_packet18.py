#!/usr/bin/env python3
import json, sys, urllib.request

BASE = "http://localhost:8000"

def post(path, data, bearer=None, timeout=30):
    url = f"{BASE}{path}"
    headers = {"Content-Type":"application/json"}
    if bearer: headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def get(path, bearer=None, timeout=30):
    url = f"{BASE}{path}"
    headers = {}
    if bearer: headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def main():
    # /version
    code, ver = get("/version")
    assert code == 200, f"/version {code}"
    for k in ("name","version","build","python"):
        assert k in ver, f"/version missing {k}"

    # readiness
    code, ready = get("/health/ready")
    assert code == 200 and ready.get("ready") is True, f"/health/ready failed: {code} {ready}"
    checks = ready.get("checks", {})
    assert checks.get("db") is True, "db readiness false"

    # env inspect (masked) requires auth
    code, reg = post("/auth/register", {"email":"packet18@example.com"})
    assert code == 200 and "access_token" in reg, f"register failed: {code} {reg}"
    tok = reg["access_token"]

    code, env = get("/ops/env?keys=AUTH_JWT_SECRET,DATABASE_URL", bearer=tok)
    assert code == 200 and "env" in env, f"/ops/env {code} {env}"
    ej = env["env"]
    assert "AUTH_JWT_SECRET" in ej and isinstance(ej["AUTH_JWT_SECRET"], (str, type(None))), "missing masked secret"
    assert "DATABASE_URL" in ej and isinstance(ej["DATABASE_URL"], (str, type(None))), "missing masked db url"
    # if present, it must include '***'
    for k in ("AUTH_JWT_SECRET","DATABASE_URL"):
        v = ej.get(k)
        if isinstance(v, str):
            assert v.startswith("***"), f"value for {k} not masked: {v!r}"

    print("PASS")

if __name__ == "__main__":
    main()