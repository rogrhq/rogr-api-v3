#!/usr/bin/env python3
import json, sys, urllib.request, subprocess

BASE = "http://localhost:8000"

def get(path, timeout=40):
    url = f"{BASE}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def main():
    # Run migrations runner (idempotent)
    rc = subprocess.call([sys.executable, "scripts/migrate_cli.py"])
    assert rc == 0, f"migrate_cli nonzero exit {rc}"

    # Readiness must be true (DB reachable)
    code, ready = get("/health/ready")
    assert code == 200 and ready.get("ready") is True, f"/health/ready failed: {code} {ready}"

    # OpenAPI exposed and includes representative routes
    code, openapi = get("/openapi.json")
    assert code == 200 and "paths" in openapi, "openapi missing paths"
    paths = openapi["paths"].keys()
    must = ["/version", "/auth/register", "/mobile/commit", "/analyses/preview"]
    missing = [p for p in must if p not in paths]
    assert not missing, f"openapi missing routes: {missing}"

    print("PASS")

if __name__ == "__main__":
    main()