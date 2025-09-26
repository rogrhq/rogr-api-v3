#!/usr/bin/env python3
import json, sys, urllib.request

BASE = "http://localhost:8000"

def _req(method, path, data=None, bearer=None, headers=None, timeout=30):
    url = f"{BASE}{path}"
    hdrs = {} if headers is None else dict(headers)
    if bearer:
        hdrs["Authorization"] = f"Bearer {bearer}"
    if data is not None and isinstance(data, (dict, list)):
        payload = json.dumps(data).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    else:
        payload = data
    req = urllib.request.Request(url, data=payload, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.getcode(), body, dict(resp.getheaders())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, body, dict(e.headers.items())

def post(path, data=None, **kw):
    return _req("POST", path, data=data, **kw)

def get(path, **kw):
    return _req("GET", path, **kw)

def main():
    # Auth to hit protected paths if needed
    code, body, hdrs = post("/auth/register", {"email":"packet19@example.com"})
    assert code == 200, f"register {code}"
    tok = json.loads(body)["access_token"]

    # A) 404 envelope + X-Request-ID auto-generated
    code, body, hdrs = get("/this/does/not/exist", bearer=tok)
    assert code == 404, f"expected 404, got {code}"
    rid = hdrs.get("x-request-id")
    assert rid and len(rid) >= 8, f"missing/short x-request-id header: {rid}"
    try:
        j = json.loads(body)
    except Exception as e:
        raise SystemExit(f"404 body not json: {body!r}")
    for k in ("error","status","detail","request_id"):
        assert k in j, f"404 envelope missing {k}"
    assert j["request_id"] == rid, "request_id mismatch between header and body"
    assert j["error"] == "http_error" and j["status"] == 404, "wrong error kind/status for 404"

    # B) Client-provided X-Request-ID is echoed + appears in body
    want_rid = "rid-test-12345"
    code, body, hdrs = get("/still/not/found", bearer=tok, headers={"X-Request-ID": want_rid})
    assert code == 404, f"expected 404"
    j = json.loads(body)
    assert hdrs.get("x-request-id") == want_rid, "header did not echo provided request id"
    assert j.get("request_id") == want_rid, "body did not echo provided request id"

    # C) Validation error envelope (422) when required field missing
    code, body, hdrs = post("/mobile/preview", {}, bearer=tok)  # missing 'text'
    assert code == 422, f"expected 422 for validation error, got {code} body={body}"
    j = json.loads(body)
    assert j.get("error") == "validation_error" and j.get("status") == 422, "wrong envelope for validation"
    assert isinstance(j.get("detail"), list) and j["detail"], "validation detail missing"
    assert "request_id" in j and hdrs.get("x-request-id") == j["request_id"], "request_id not present/matching"

    print("PASS")

if __name__ == "__main__":
    main()