#!/usr/bin/env python3
import json
import urllib.request
import urllib.error

ORIGIN = "http://localhost:19006"

def _lower_headers(hdrs):
    return {k.lower(): v for k, v in hdrs.items()}

def _req(url, method="GET", data=None, headers=None):
    headers = headers or {}
    if data is not None and not isinstance(data, (bytes, bytearray)):
        data = json.dumps(data).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    return urllib.request.urlopen(req, timeout=15)

def main():
    # Preflight OPTIONS (should return ACAO)
    try:
        resp = _req(
            "http://localhost:8000/auth/register",
            method="OPTIONS",
            headers={
                "Origin": ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization",
            },
        )
        hdrs = _lower_headers(resp.headers)
        assert "access-control-allow-origin" in hdrs, f"Missing ACAO on OPTIONS; got {dict(resp.headers)}"
    except urllib.error.HTTPError as e:
        raise AssertionError(f"OPTIONS failed: {e.code} {e.reason}")

    # Actual POST (must include Origin header too)
    resp = _req(
        "http://localhost:8000/auth/register",
        method="POST",
        data={"email": "test@example.com", "password": "hunter2"},
        headers={"Origin": ORIGIN},
    )
    hdrs = _lower_headers(resp.headers)
    assert "access-control-allow-origin" in hdrs, f"CORS header missing on POST /auth/register; got {dict(resp.headers)}"
    print("PASS: Packet 13 CORS headers present on OPTIONS and POST")

if __name__ == "__main__":
    main()