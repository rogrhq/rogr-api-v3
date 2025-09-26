#!/usr/bin/env python3
import json, sys, time, urllib.request

BASE = "http://localhost:8000"

def post(path, data_bytes_or_obj, bearer=None, content_type="application/json", timeout=30):
    url = f"{BASE}{path}"
    if isinstance(data_bytes_or_obj, (bytes, bytearray)):
        payload = data_bytes_or_obj
    else:
        payload = json.dumps(data_bytes_or_obj).encode("utf-8")
    headers = {"Content-Type": content_type}
    if bearer: headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode(), resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, body

def get(path, bearer=None, timeout=30):
    url = f"{BASE}{path}"
    headers = {}
    if bearer: headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode(), resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, body

def main():
    # Register + token
    code, body = post("/auth/register", {"email":"packet16@example.com"})
    assert code == 200, f"register expected 200 got {code}"
    tok = json.loads(body)["access_token"]

    # 1) Unsupported media type on write endpoint
    code, body = post("/mobile/preview", "not-json".encode("utf-8"), bearer=tok, content_type="text/plain")
    assert code == 415, f"expected 415 for non-json, got {code} body={body}"

    # 2) Request body too large (exceeds MAX_BODY_BYTES set by test env)
    big = b"x" * (15 * 1024)  # 15 KiB; test env sets MAX_BODY_BYTES=10240
    code, body = post("/mobile/preview", big, bearer=tok, content_type="application/json")
    assert code == 413, f"expected 413 for large body, got {code}"

    # 3) Rate limit: hit /auth/me more than RATE_LIMIT_PER_MINUTE (set low in test env)
    # First, get /auth/me a few times to exceed threshold 5
    exceeded = False
    for i in range(8):
        code, _ = get("/auth/me", bearer=tok)
        if code == 429:
            exceeded = True
            break
        elif code != 200:
            raise SystemExit(f"/auth/me unexpected status {code}")
    assert exceeded, "expected to hit rate limit (429) but did not"

    print("PASS")

if __name__ == "__main__":
    main()