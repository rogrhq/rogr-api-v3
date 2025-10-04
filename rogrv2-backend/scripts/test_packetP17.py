import os
import sys
import time
from typing import Dict, Any, List
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure repo root on path
_HERE = Path(__file__).resolve()
_ROOT = _HERE.parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import importlib
m = importlib.import_module("main")
app = m.app
client = TestClient(app)

CLAIM_TEXT = "Austin increased its 2024 city budget by 8%."

# Configure modest fetch budget to keep latency reasonable
os.environ.setdefault("ROGR_FETCH_TOPK_PER_ARM", "2")
os.environ.setdefault("ROGR_FETCH_EXPLORE_PER_ARM", "0")


def get_token() -> str:
    email = f"p17.test.{int(time.time()*1000)}@example.com"
    r = client.post("/auth/register", json={"email": email})
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    j = r.json()
    tok = j.get("access_token") or j.get("token")
    assert tok, f"no token in register response: {j}"
    return tok


def preview(claim: str, tok: str):
    return client.post("/analyses/preview", json={"text": claim}, headers={"Authorization": f"Bearer {tok}"})


def _count_enriched(items: List[Dict[str, Any]], min_chars: int = 400) -> int:
    n = 0
    for it in items:
        cc = it.get("content_chars")
        ex = it.get("content_excerpt")
        if isinstance(cc, int) and cc >= min_chars:
            n += 1
        elif isinstance(ex, str) and len(ex) >= 200:
            n += 1
    return n


def main() -> None:
    tok = get_token()
    t0 = time.monotonic()
    r = preview(CLAIM_TEXT, tok)
    dt = time.monotonic() - t0
    assert r.status_code == 200, f"preview failed: {r.status_code} {r.text}"
    assert dt < 15.0, f"preview too slow: {dt:.2f}s"

    j = r.json()
    claims = j.get("claims")
    assert isinstance(claims, list) and len(claims) > 0, "claims missing/empty"
    c0 = claims[0]

    ev = (c0 or {}).get("evidence") or {}
    armA = ev.get("arm_A") or []
    armB = ev.get("arm_B") or []
    assert isinstance(armA, list) and isinstance(armB, list) and armA and armB, "evidence arms missing/empty"

    # Verify fetch budget not exceeded
    topk = int(os.environ.get("ROGR_FETCH_TOPK_PER_ARM", "2"))
    explore = int(os.environ.get("ROGR_FETCH_EXPLORE_PER_ARM", "0"))
    max_fetch = topk + explore
    fetchedA = sum(1 for it in armA[:max_fetch] if it.get("content_chars") or it.get("content_status") is not None)
    fetchedB = sum(1 for it in armB[:max_fetch] if it.get("content_chars") or it.get("content_status") is not None)
    assert fetchedA <= max_fetch and fetchedB <= max_fetch, "fetch budget exceeded"

    # At least one enriched item per arm
    assert _count_enriched(armA) >= 1, "no enriched content on arm_A"
    assert _count_enriched(armB) >= 1, "no enriched content on arm_B"

    # Verdict still present (from P16)
    verdict = (c0 or {}).get("verdict")
    assert isinstance(verdict, dict) and "label" in verdict and "confidence" in verdict, "verdict missing after enrichment"

    print("P17: enriched counts:", _count_enriched(armA), _count_enriched(armB))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"PACKET FAIL P17: {e}")
        sys.exit(1)
    print("PACKET PASS P17")
    sys.exit(0)
