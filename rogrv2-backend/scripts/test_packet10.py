#!/usr/bin/env python3
import json, sys, urllib.request, pathlib, os

ROOT = pathlib.Path(__file__).resolve().parents[1]

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

def read_contract(name):
    p = ROOT / "frontend_contracts" / "v1" / name
    assert p.exists(), f"missing contract file: {p}"
    return json.loads(p.read_text(encoding="utf-8"))

def main():
    # Register to get a token
    code, reg = post("http://localhost:8000/auth/register", {"email":"contracts@example.com"})
    assert code == 200 and "access_token" in reg, f"register failed: {code} {reg}"
    tok = reg["access_token"]

    # /auth/me
    code, me = get("http://localhost:8000/auth/me", bearer=tok)
    assert code == 200, f"/auth/me {code}"
    want_me = read_contract("auth_me.json")
    # Only check keys/types; values (sub, exp) are dynamic
    for k in ("sub","roles","exp"):
        assert k in me, f"/auth/me missing key {k}"
    assert isinstance(me["roles"], list) and "user" in me["roles"], "/auth/me roles must include 'user'"

    # /feed
    code, feed = get("http://localhost:8000/feed", bearer=tok)
    assert code == 200, f"/feed {code}"
    want_feed = read_contract("feed.json")
    # Contract keys present and shapes align
    assert "items" in feed and isinstance(feed["items"], list), "/feed items"
    assert "next_cursor" in feed, "/feed next_cursor"
    assert feed["items"], "/feed empty items"
    # Check one item has required keys
    item = feed["items"][0]
    for k in ("id","analysis_id","author_handle","visibility","created_at","headline","overall"):
        assert k in item, f"/feed item missing {k}"
    assert "score" in item["overall"] and "label" in item["overall"], "/feed item overall shape"

    # /archive/search
    code, arch = get("http://localhost:8000/archive/search?q=budget", bearer=tok)
    assert code == 200, f"/archive/search {code}"
    want_arch = read_contract("archive_search.json")
    for k in ("query","filters","results","next_cursor"):
        assert k in arch, f"/archive/search missing {k}"
    assert isinstance(arch["results"], list) and arch["results"], "/archive/search results empty"
    r0 = arch["results"][0]
    for k in ("analysis_id","created_at","claims","overall"):
        assert k in r0, f"/archive/search result missing {k}"

    print("PASS")

if __name__ == "__main__":
    main()