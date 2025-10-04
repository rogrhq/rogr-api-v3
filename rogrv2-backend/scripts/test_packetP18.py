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

# Keep same fetch budget from P17
os.environ.setdefault("ROGR_FETCH_TOPK_PER_ARM", "2")
os.environ.setdefault("ROGR_FETCH_EXPLORE_PER_ARM", "0")

ALLOWED_STANCES = {"support", "challenge", "mixed", "unrelated"}


def get_token() -> str:
    email = f"p18.test.{int(time.time()*1000)}@example.com"
    r = client.post("/auth/register", json={"email": email})
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    j = r.json()
    tok = j.get("access_token") or j.get("token")
    assert tok, f"no token in register response: {j}"
    return tok


def preview(claim: str, tok: str):
    return client.post("/analyses/preview", json={"text": claim}, headers={"Authorization": f"Bearer {tok}"})


def _aligned_count(items: List[Dict[str, Any]]) -> int:
    n = 0
    for it in items:
        al = it.get("alignment") or {}
        if isinstance(al, dict) and (al.get("entity_hit") or al.get("number_hit") or al.get("year_hit")):
            if isinstance(it.get("matches"), list) and len(it.get("matches")) > 0:
                n += 1
    return n


def _sum_content(items: List[Dict[str, Any]], k: int = 3) -> float:
    # sum of top-k content_score (fallback to score)
    eff = []
    for it in items:
        cs = it.get("content_score")
        if isinstance(cs, (int, float)) and cs > 0:
            eff.append(float(cs))
        else:
            eff.append(float(it.get("score", 0.0)))
    eff.sort(reverse=True)
    return sum(eff[:max(0, k)])


def main() -> None:
    tok = get_token()
    t0 = time.monotonic()
    r = preview(CLAIM_TEXT, tok)
    dt = time.monotonic() - t0
    assert r.status_code == 200, f"preview failed: {r.status_code} {r.text}"
    assert dt < 18.0, f"preview too slow: {dt:.2f}s"

    j = r.json()
    claims = j.get("claims")
    assert isinstance(claims, list) and len(claims) > 0, "claims missing/empty"
    c0 = claims[0]

    ev = (c0 or {}).get("evidence") or {}
    armA = ev.get("arm_A") or []
    armB = ev.get("arm_B") or []
    assert isinstance(armA, list) and isinstance(armB, list) and armA and armB, "evidence arms missing/empty"

    # Alignment presence per arm
    assert _aligned_count(armA) >= 1, "no aligned item on arm_A"
    assert _aligned_count(armB) >= 1, "no aligned item on arm_B"

    # Stance field present and valid on at least one aligned item per arm
    def _has_stance(items):
        for it in items:
            if it.get("alignment") and it.get("matches"):
                st = it.get("item_stance")
                if isinstance(st, str) and st in ALLOWED_STANCES:
                    return True
        return False
    assert _has_stance(armA), "missing item_stance on arm_A"
    assert _has_stance(armB), "missing item_stance on arm_B"

    # Verdict still present, and roughly consistent with content sums when content present
    verdict = (c0 or {}).get("verdict")
    assert isinstance(verdict, dict) and "label" in verdict and "confidence" in verdict, "verdict missing"

    # If content_score shows up, sanity-check label vs content sums
    if any(isinstance((x or {}).get("content_score"), (int, float)) and (x.get("content_score") or 0) > 0 for x in (armA + armB)):
        sA = _sum_content(armA, k=3)
        sB = _sum_content(armB, k=3)
        label = str(verdict.get("label")).lower()
        diff = sA - sB
        if label == "support":
            assert diff >= -0.15, f"support label contradicts content sums: diff={diff:.3f}"
        elif label == "challenge":
            assert diff <= 0.15, f"challenge label contradicts content sums: diff={diff:.3f}"
        elif label == "mixed":
            assert abs(diff) <= 0.50, f"mixed label inconsistent with content sums: diff={diff:.3f}"

    print("P18: aligned A,B counts:", _aligned_count(armA), _aligned_count(armB))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"PACKET FAIL P18: {e}")
        sys.exit(1)
    print("PACKET PASS P18")
    sys.exit(0)
