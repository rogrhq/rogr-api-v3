#!/usr/bin/env python3
"""
P29 LIVE test:
- Ensures p29 wrapper installs and executes on API preview.
- Verifies run_manifest, replay_id, diversified flag.
- Confirms researchers[*].lane_config.knobs and telemetry, and provider parity.
"""
import os
import json
import importlib
from typing import Any, Dict
from fastapi.testclient import TestClient

# Ensure wrappers are importable early
import sitecustomize  # noqa: F401
import intelligence.content.p28_diversify  # ensure P28 present
import intelligence.content.p29_diversify_controls  # this packet

import main  # repo root main.py
app = getattr(main, "app")

def _bearer(client: TestClient) -> Dict[str, str]:
    r = client.post("/auth/register", json={"email": "p29.test@user.com"})
    r.raise_for_status()
    tok = r.json().get("access_token") or ""
    return {"Authorization": f"Bearer {tok}"}

def _assert(cond: bool, msg: str):
    if not cond:
        raise AssertionError(msg)

def main_test():
    client = TestClient(app)
    hdrs = _bearer(client)
    body = {"text": "Austin increased its 2024 city budget by 8%", "mode": "live"}

    # Hit API
    r = client.post("/analyses/preview", json=body, headers=hdrs)
    r.raise_for_status()
    j = r.json()

    # Basic shape
    _assert(isinstance(j, dict), "response not dict")
    claims = j.get("claims") or []
    _assert(len(claims) >= 1, "no claims in response")
    c0 = claims[0]
    researchers = c0.get("researchers") or []
    _assert(len(researchers) >= 2, "need two researchers (R1,R2)")

    # Manifest and diversified flag
    manifest = j.get("run_manifest") or {}
    _assert(isinstance(manifest, dict), "run_manifest missing")
    _assert(bool(manifest.get("replay_id")), "replay_id missing")
    _assert(bool(j.get("diversified")), "diversified flag missing")

    # Lane parity & telemetry
    r1, r2 = researchers[0], researchers[1]
    lc1 = (r1.get("lane_config") or {})
    lc2 = (r2.get("lane_config") or {})
    prov1 = lc1.get("providers") or []
    prov2 = lc2.get("providers") or []
    _assert(set(prov1) == set(prov2), "provider set parity failed")

    # knobs present
    k1 = (lc1.get("knobs") or {})
    k2 = (lc2.get("knobs") or {})
    for k in ("query_shuffle","timeout_jitter_ms","max_per_provider","seed"):
        _assert(k in k1, f"knob {k} missing on R1")
        _assert(k in k2, f"knob {k} missing on R2")

    # telemetry present (counts may be zero if provider gave no results, but structure must exist)
    t1 = r1.get("telemetry") or {}
    t2 = r2.get("telemetry") or {}
    _assert("providers" in t1, "telemetry.providers missing R1")
    _assert("providers" in t2, "telemetry.providers missing R2")
    _assert("duration_ms" in t1, "telemetry.duration_ms missing R1")
    _assert("duration_ms" in t2, "telemetry.duration_ms missing R2")

    # manifest lanes mirror lane_config providers
    lanes = (manifest.get("lanes") or {})
    m1 = (lanes.get("R1") or {}).get("providers") or []
    m2 = (lanes.get("R2") or {}).get("providers") or []
    _assert(m1 == prov1 or set(m1) == set(prov1), "manifest R1 providers mismatch")
    _assert(m2 == prov2 or set(m2) == set(prov2), "manifest R2 providers mismatch")

    print("PACKET PASS P29")

if __name__ == "__main__":
    main_test()
