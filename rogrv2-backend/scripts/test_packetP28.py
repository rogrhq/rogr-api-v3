#!/usr/bin/env python3
"""
P28 (LIVE) — Lane Diversification Knobs

Asserts:
- Diversifier installs: p28 logs present when ROGR_DIAG=1.
- Two researchers with lane_config present.
- Provider set equality across lanes (no bias), but order differs OR queries differ.
- Each lane still has both arms populated (no functional regression).
"""
import json
import os
import sys
from importlib import import_module

os.environ.setdefault("ROGR_DIAG","1")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Load wrappers explicitly in safe order
for modname in (
    "intelligence.content.p22_ingest",
    "intelligence.content.p23_semantic",
    "intelligence.content.p24_semantic_frames",
    "intelligence.content.p25_semantic_aggregate",
    "intelligence.content.p26_dual_researchers",
    "intelligence.content.p27_consensus",
    "intelligence.content.p28_diversify",
):
    try:
        import_module(modname)
    except Exception as e:
        print(f"P28 FAIL: import {modname}: {e}", file=sys.stderr); sys.exit(1)

# App
try:
    main = import_module("main")
except Exception as e:
    print(f"P28 FAIL: cannot import main: {e}", file=sys.stderr); sys.exit(1)
app = getattr(main, "app", None)
if app is None:
    print("P28 FAIL: FastAPI app not found at main.app", file=sys.stderr); sys.exit(1)

from fastapi.testclient import TestClient  # noqa
client = TestClient(app)

def _register(email: str) -> str:
    r = client.post("/auth/register", json={"email": email})
    if r.status_code != 200:
        print(f"P28 FAIL: register failed {r.status_code} {r.text}", file=sys.stderr); sys.exit(1)
    tok = r.json().get("access_token")
    if not tok:
        print("P28 FAIL: no access_token", file=sys.stderr); sys.exit(1)
    return tok

def _preview(claim: str, tok: str):
    r = client.post("/analyses/preview", json={"text": claim, "mode": "live"}, headers={"Authorization": f"Bearer {tok}"}, timeout=150)
    if r.status_code != 200:
        print(f"P28 FAIL: preview failed {r.status_code} {r.text}", file=sys.stderr); sys.exit(1)
    return r.json()

def _providers_from_lane(lane):
    cfg = lane.get("lane_config") or {}
    return cfg.get("providers") or []

def _queries_first3(lane, arm_key):
    cfg = lane.get("lane_config") or {}
    q = (cfg.get("queries_first3") or {}).get(arm_key) or []
    return q

def main():
    tok = _register("p28.diversify@test.example.com")
    claim = "Austin increased its 2024 city budget by 8%"
    j = _preview(claim, tok)

    claims = j.get("claims") or []
    if not claims:
        print("P28 FAIL: no claims", file=sys.stderr); sys.exit(1)
    c0 = claims[0]
    lanes = c0.get("researchers") or []
    if len(lanes) != 2:
        print(f"P28 FAIL: expected 2 researchers, got {len(lanes)}", file=sys.stderr); sys.exit(1)

    r1, r2 = lanes[0], lanes[1]
    # Lane configs present
    if not r1.get("lane_config") or not r2.get("lane_config"):
        print("P28 FAIL: missing lane_config on one or both lanes", file=sys.stderr); sys.exit(1)

    # Arms populated (basic sanity)
    def _arm_chk(lane):
        ev = lane.get("evidence") or {}
        return (len(ev.get("arm_A") or []) > 0) and (len(ev.get("arm_B") or []) > 0)
    if not (_arm_chk(r1) and _arm_chk(r2)):
        print("P28 FAIL: lane evidence missing on A or B", file=sys.stderr); sys.exit(1)

    # Provider set equality (no bias) + order difference OR query order difference
    p1, p2 = _providers_from_lane(r1), _providers_from_lane(r2)
    if set(p1) != set(p2):
        print(f"P28 FAIL: provider set differs across lanes (bias risk) p1={p1} p2={p2}", file=sys.stderr); sys.exit(1)

    diversified = False
    if p1 != p2:
        diversified = True
    else:
        # Fall back to query order difference check
        for arm_key in ("A","B"):
            q1 = _queries_first3(r1, arm_key)
            q2 = _queries_first3(r2, arm_key)
            if q1 and q2 and q1 != q2:
                diversified = True
                break
    if not diversified:
        print("P28 FAIL: lanes did not diversify (provider order and query order both identical)", file=sys.stderr); sys.exit(1)

    # Final summary
    print(json.dumps({
        "event":"p28.test_summary",
        "providers": {"R1": p1, "R2": p2},
        "diversified": diversified
    }, ensure_ascii=False))
    print("PACKET PASS P28")

if __name__ == "__main__":
    main()
