#!/usr/bin/env python3
import json, sys, urllib.request

def post(url, data, headers=None, bearer=None):
    h = {"Content-Type":"application/json"}
    if headers: h.update(headers)
    if bearer: h["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=h)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        return resp.getcode(), json.loads(body)

def main():
    # 1) register to get token
    code, reg = post("http://localhost:8000/auth/register", {"email":"audit@example.com"})
    assert code == 200 and "access_token" in reg, f"register failed: {code} {reg}"
    tok = reg["access_token"]

    # 2) call preview in offline deterministic mode
    code, body = post("http://localhost:8000/analyses/preview", {"text":"Austin increased its 2024 city budget by 8%.", "test_mode": True}, bearer=tok)
    assert code == 200, f"preview failed: {code}"
    assert "claims" in body and isinstance(body["claims"], list) and body["claims"], "missing claims"
    assert "overall" in body and "score" in body["overall"], "missing overall score"

    # 3) methodology capsule present and well-formed
    m = body.get("methodology", {})
    assert isinstance(m, dict), "missing methodology"
    for key in ("version","provider_set","strategy","test_mode","counts","events"):
        assert key in m, f"methodology missing {key}"
    assert m["strategy"] == "A/B"
    assert m["test_mode"] is True
    assert isinstance(m["provider_set"], list) and m["provider_set"] == ["offline-synth"]
    assert isinstance(m["events"], list) and len(m["events"]) >= 5, "expected multiple audit events"
    names = [e.get("stage") for e in m["events"]]
    # required stages
    for req in ("start","extract_done","plan_done","gather_done","consensus_done","score_done","finalize"):
        assert req in names, f"missing audit stage: {req}"
    # event records must have timestamp
    assert all("ts" in e for e in m["events"]), "events must carry ts"

    print("PASS")

if __name__ == "__main__":
    main()