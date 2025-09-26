#!/usr/bin/env python3
import json, sys, urllib.request, hashlib

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

def canonical_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha256_hex(b):
    return hashlib.sha256(b).hexdigest()

def main():
    # auth
    code, reg = post("/auth/register", {"email":"packet17@example.com"})
    assert code == 200 and "access_token" in reg, f"register failed: {code} {reg}"
    tok = reg["access_token"]

    # 1) Preview export
    code, bundle = post("/analyses/export/ifcn_preview", {"text":"Austin increased its 2024 city budget by 8%.", "test_mode": True}, bearer=tok)
    assert code == 200, f"ifcn_preview {code}"
    for k in ("schema_version","input","claims","overall","methodology","evidence_ledger","checksum"):
        assert k in bundle, f"bundle missing {k}"
    assert bundle["schema_version"] == "1.0", "schema_version mismatch"
    assert "version" in bundle["methodology"], "methodology missing version"
    # verify checksum
    wo = dict(bundle); wo.pop("checksum", None)
    expect = sha256_hex(canonical_bytes(wo))
    got = bundle["checksum"]["sha256"]
    assert got == expect, f"checksum mismatch: got {got} expect {expect}"

    # 2) Persist one analysis and export by id (minimal ledger acceptable)
    code, commit = post("/mobile/commit", {"text":"Austin increased its 2024 city budget by 8%.", "test_mode": True}, bearer=tok)
    assert code == 200 and "analysis_id" in commit, f"commit failed: {code} {commit}"
    aid = commit["analysis_id"]

    code, pb = get(f"/analyses/{aid}/export/ifcn", bearer=tok)
    assert code == 200, f"persisted export {code}"
    for k in ("schema_version","input","claims","overall","methodology","evidence_ledger","checksum"):
        assert k in pb, f"persisted bundle missing {k}"
    # checksum valid again
    wo2 = dict(pb); wo2.pop("checksum", None)
    expect2 = sha256_hex(canonical_bytes(wo2))
    got2 = pb["checksum"]["sha256"]
    assert got2 == expect2, "persisted checksum mismatch"

    print("PASS")

if __name__ == "__main__":
    main()