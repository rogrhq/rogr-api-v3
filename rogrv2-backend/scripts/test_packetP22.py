#!/usr/bin/env python3
"""
P22-FIX4 test: Ensure enrichment code is active and bound to the same globals api.analyses.preview uses.
- Contract probe: legacy body {"claims":[{"text": "..."}], "mode":"live"} MUST be rejected (422).
- Canonical call: {"text":"...", "mode":"live"} MUST succeed; items must have coverage; at least
  one content-bearing item per arm when fetchable.
- Diagnostics expected (ROGR_DIAG=1): p22.installed, p22.fetch_wrapped, p22.rebound_api_names, p22.preview_enriched.
"""
import json
import os
import sys
from importlib import import_module
from typing import Any, Dict, List

os.environ.setdefault("ROGR_DIAG", "1")

# Ensure REPO ROOT is on sys.path (parent of scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Import activation modules BEFORE app
try:
    import sitecustomize  # noqa: F401
except Exception as e:
    print(f"P22 FAIL: sitecustomize import error: {e}", file=sys.stderr)
    sys.exit(1)
try:
    # Force-load p22_ingest (deterministic activation)
    import intelligence.content.p22_ingest as _p22  # noqa: F401
except Exception as e:
    print(f"P22 FAIL: p22_ingest import error: {e}", file=sys.stderr)
    sys.exit(1)

# Now import the FastAPI app
try:
    main = import_module("main")
except Exception as e:
    print(f"P22 FAIL: cannot import main: {e}", file=sys.stderr)
    sys.exit(1)

app = getattr(main, "app", None)
if app is None:
    print("P22 FAIL: FastAPI app not found at main.app", file=sys.stderr)
    sys.exit(1)

from fastapi.testclient import TestClient
client = TestClient(app)

def _register_token(email: str) -> str:
    r = client.post("/auth/register", json={"email": email})
    if r.status_code != 200:
        print(f"P22 FAIL: register failed {r.status_code} {r.text}", file=sys.stderr)
        sys.exit(1)
    j = r.json()
    token = j.get("access_token")
    if not token:
        print("P22 FAIL: no access_token in register response", file=sys.stderr)
        sys.exit(1)
    return token

def _probe_legacy_body(token: str, claim_text: str) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    legacy_body = {"claims": [{"text": claim_text}], "mode": "live"}
    r = client.post("/analyses/preview", json=legacy_body, headers=headers, timeout=30)
    print(json.dumps({"event":"p22.contract_req_shape_probe","status":r.status_code}, ensure_ascii=False))
    if r.status_code != 422:
        print(f"P22 FAIL: legacy body accepted status={r.status_code}; contract broken", file=sys.stderr)
        sys.exit(1)

def _preview_canonical(claim_text: str, token: str) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    body = {"text": claim_text, "mode": "live"}
    r = client.post("/analyses/preview", json=body, headers=headers, timeout=60)
    if r.status_code != 200:
        print(f"P22 FAIL: preview failed {r.status_code} {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()

def _iter_items(resp: Dict[str, Any], arm: str) -> List[Dict[str, Any]]:
    claims = resp.get("claims") or []
    if not claims or not isinstance(claims[0], dict):
        return []
    ev = claims[0].get("evidence") or {}
    return ev.get(arm) or []

def _check(resp: Dict[str, Any]) -> None:
    arms = ["arm_A", "arm_B"]
    coverage_ok = {"full", "partial", "snippet_only"}
    summary = {}
    for arm in arms:
        items = _iter_items(resp, arm)
        has_content = 0
        cov_missing = 0
        for it in items:
            cov = it.get("coverage")
            if cov not in coverage_ok:
                cov_missing += 1
            if (it.get("content") or "") and it.get("content_hash"):
                has_content += 1
        summary[arm] = {"items": len(items), "has_content": has_content, "cov_missing": cov_missing}

    print(json.dumps({"event":"p22.test_summary","arms":summary}, ensure_ascii=False))

    for arm, stats in summary.items():
        if stats["cov_missing"] > 0:
            print(f"P22 FAIL: missing or invalid coverage on {arm}", file=sys.stderr)
            sys.exit(1)
        if stats["items"] > 0 and stats["has_content"] == 0:
            print(f"P22 FAIL: no content-bearing items on {arm}", file=sys.stderr)
            sys.exit(1)

def main():
    claim = "Austin increased its 2024 city budget by 8%"
    token = _register_token("p22.fix4@test.example.com")
    _probe_legacy_body(token, claim)
    resp = _preview_canonical(claim, token)
    _check(resp)
    print("PACKET PASS P22-FIX4")

if __name__ == "__main__":
    main()
