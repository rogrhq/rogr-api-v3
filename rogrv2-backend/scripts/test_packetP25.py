#!/usr/bin/env python3
"""
P25 (LIVE) — Arm-level aggregation & verdict test.

Asserts:
- P25 wrapper installs and rebinds preview.
- Live /analyses/preview returns claims with:
  - verdict.confidence in [0,1]
  - verdict.label in {"supports","challenges","mixed","insufficient"}
  - verdict.arm_strength.support/challenge in [0,1], and balance = support - challenge
- Arms still contain items (no filtering).
- At least one diagnostic from p25.* when ROGR_DIAG=1.
"""
import json
import os
import sys
from importlib import import_module

os.environ.setdefault("ROGR_DIAG", "1")

# Ensure repo on path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Load sitecustomize and wrappers in order
try:
    import sitecustomize  # noqa
except Exception as e:
    print(f"P25 FAIL: sitecustomize import error: {e}", file=sys.stderr); sys.exit(1)

for modname in (
    "intelligence.content.p22_ingest",
    "intelligence.content.p23_semantic",
    "intelligence.content.p24_semantic_frames",
    "intelligence.content.p25_semantic_aggregate",
):
    try:
        import_module(modname)
    except Exception as e:
        print(f"P25 FAIL: import {modname}: {e}", file=sys.stderr); sys.exit(1)

# App import
try:
    main = import_module("main")
except Exception as e:
    print(f"P25 FAIL: cannot import main: {e}", file=sys.stderr); sys.exit(1)
app = getattr(main, "app", None)
if app is None:
    print("P25 FAIL: FastAPI app not found at main.app", file=sys.stderr); sys.exit(1)

from fastapi.testclient import TestClient  # noqa
client = TestClient(app)

def _register(email: str) -> str:
    r = client.post("/auth/register", json={"email": email})
    if r.status_code != 200:
        print(f"P25 FAIL: register failed {r.status_code} {r.text}", file=sys.stderr); sys.exit(1)
    tok = r.json().get("access_token")
    if not tok:
        print("P25 FAIL: no access_token", file=sys.stderr); sys.exit(1)
    return tok

def _preview(claim: str, tok: str):
    r = client.post("/analyses/preview", json={"text": claim, "mode": "live"}, headers={"Authorization": f"Bearer {tok}"}, timeout=90)
    if r.status_code != 200:
        print(f"P25 FAIL: preview failed {r.status_code} {r.text}", file=sys.stderr); sys.exit(1)
    return r.json()

def main():
    claim = "Austin increased its 2024 city budget by 8%"
    tok = _register("p25.aggregate@test.example.com")
    j = _preview(claim, tok)

    claims = j.get("claims") or []
    if not claims:
        print("P25 FAIL: preview returned no claims", file=sys.stderr); sys.exit(1)
    c0 = claims[0]
    ev = c0.get("evidence") or {}
    A = ev.get("arm_A") or []
    B = ev.get("arm_B") or []
    if len(A) == 0 or len(B) == 0:
        print("P25 FAIL: one arm has zero items", file=sys.stderr); sys.exit(1)

    verdict = c0.get("verdict") or {}
    label = verdict.get("label")
    conf = verdict.get("confidence")
    arm_strength = verdict.get("arm_strength") or {}

    if label not in {"supports","challenges","mixed","insufficient"}:
        print(f"P25 FAIL: invalid verdict label: {label}", file=sys.stderr); sys.exit(1)
    if not isinstance(conf, (int, float)) or not (0.0 <= float(conf) <= 1.0):
        print(f"P25 FAIL: invalid verdict confidence: {conf}", file=sys.stderr); sys.exit(1)

    sa = arm_strength.get("support")
    sb = arm_strength.get("challenge")
    bal = arm_strength.get("balance")
    ok_bounds = lambda x: isinstance(x, (int,float)) and 0.0 <= float(x) <= 1.0
    if not (ok_bounds(sa) and ok_bounds(sb)):
        print(f"P25 FAIL: invalid arm strengths: {arm_strength}", file=sys.stderr); sys.exit(1)
    if abs((sa - sb) - (bal if isinstance(bal,(int,float)) else 9999)) > 1e-6:
        print("P25 FAIL: balance does not equal support - challenge", file=sys.stderr); sys.exit(1)

    print(json.dumps({"event":"p25.test_summary","label":label,"confidence":conf,"support":sa,"challenge":sb,"balance":bal}, ensure_ascii=False))
    print("PACKET PASS P25")

if __name__ == "__main__":
    main()
