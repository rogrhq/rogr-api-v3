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
ALLOWED_PROVIDERS = {"brave", "google", "bing"}


def get_token() -> str:
    email = f"p15.test.{int(time.time()*1000)}@example.com"
    r = client.post("/auth/register", json={"email": email})
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    j = r.json()
    tok = j.get("access_token") or j.get("token")
    assert tok, f"no token in register response: {j}"
    return tok


def preview(claim: str, tok: str):
    return client.post("/analyses/preview", json={"text": claim}, headers={"Authorization": f"Bearer {tok}"})


def assert_ranked(evs: List[Dict[str, Any]]):
    assert isinstance(evs, list) and len(evs) > 0, "evidence empty"
    # Scores and ranks must be present and monotonic
    scores = [it.get("score") for it in evs]
    ranks = [it.get("rank") for it in evs]
    assert all(isinstance(s, (int, float)) for s in scores), "missing numeric score"
    # Score range sanity for P15: scores must be within [0, 1]
    assert all(0.0 <= float(s) <= 1.0 for s in scores), "score out of [0,1]"
    assert all(isinstance(r, int) and r >= 1 for r in ranks), "missing rank"
    # non-increasing scores and strictly increasing ranks
    assert all(scores[i] >= scores[i+1] - 1e-9 for i in range(len(scores)-1)), "scores not sorted desc"
    assert ranks == list(range(1, len(ranks)+1)), "ranks not 1..N"
    # shape checks
    for it in evs:
        assert it.get("provider") in ALLOWED_PROVIDERS, "bad provider"
        assert it.get("url"), "missing url"
        assert it.get("title") is not None, "missing title"
        assert it.get("snippet") is not None, "missing snippet"
        assert it.get("arm") in {"A", "B"}, "bad arm"


def main() -> None:
    tok = get_token()
    t0 = time.monotonic()
    r = preview(CLAIM_TEXT, tok)
    dt = time.monotonic() - t0
    assert r.status_code == 200, f"preview failed: {r.status_code} {r.text}"
    assert dt < 12.0, f"preview too slow: {dt:.2f}s"
    j = r.json()
    claims = j.get("claims")
    assert isinstance(claims, list) and len(claims) > 0, "claims missing/empty"
    ev = (claims[0] or {}).get("evidence") or {}
    armA = ev.get("arm_A") or []
    armB = ev.get("arm_B") or []
    assert_ranked(armA)
    assert_ranked(armB)
    # Global dedupe sanity: no duplicate canonical URLs across both arms
    urls = [it.get("url") for it in (armA + armB) if it.get("url")]
    assert len(urls) == len(set(urls)), "duplicate URLs present across arms"
    # Canonicalization sanity: URLs should not contain fragments
    assert all('#' not in u for u in urls), "URL contains fragment (#)"
    print("P15: ranked A,B sizes:", len(armA), len(armB))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"PACKET FAIL P15: {e}")
        sys.exit(1)
    print("PACKET PASS P15")
    sys.exit(0)
