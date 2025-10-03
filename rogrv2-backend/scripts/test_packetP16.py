import os
import sys
import time
import json
from typing import Dict, Any, List, Tuple, Optional
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
ALLOWED_LABELS = {"support", "challenge", "mixed", "insufficient"}
ALLOWED_PROVIDERS = {"brave", "google", "bing"}


def get_token() -> str:
    email = f"p16.test.{int(time.time()*1000)}@example.com"
    r = client.post("/auth/register", json={"email": email})
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    j = r.json()
    tok = j.get("access_token") or j.get("token")
    assert tok, f"no token in register response: {j}"
    return tok


def preview(claim: str, tok: str):
    return client.post("/analyses/preview", json={"text": claim}, headers={"Authorization": f"Bearer {tok}"})


def _score_sum(items: List[Dict[str, Any]], k: int = 3) -> float:
    # sum of top-k scores; assumes items already ranked desc
    s = 0.0
    for it in items[:max(0, k)]:
        try:
            s += float(it.get("score", 0.0))
        except Exception:
            s += 0.0
    return s


def _extract_refs(verdict: Dict[str, Any]) -> List[Any]:
    # Support multiple possible fields, be generous
    refs = verdict.get("rationale_refs")
    if refs is None:
        refs = verdict.get("rationale")
    if refs is None:
        refs = verdict.get("refs")
    if refs is None:
        return []
    return refs if isinstance(refs, list) else []


def _refs_map_to_evidence(refs: List[Any], armA: List[Dict[str, Any]], armB: List[Dict[str, Any]]) -> Tuple[int,int]:
    # Count how many refs map to A vs B by URL
    urlsA = {it.get("url") for it in armA}
    urlsB = {it.get("url") for it in armB}
    a,b = 0,0
    for r in refs:
        url = None
        if isinstance(r, dict):
            url = r.get("url") or r.get("href")
        elif isinstance(r, str):
            url = r
        elif isinstance(r, int):
            # if index, try into concatenated list
            all_items = armA + armB
            if 0 <= r < len(all_items):
                url = all_items[r].get("url")
        if url in urlsA:
            a += 1
        elif url in urlsB:
            b += 1
    return a,b


def main() -> None:
    # Auth and latency
    tok = get_token()
    t0 = time.monotonic()
    r = preview(CLAIM_TEXT, tok)
    dt = time.monotonic() - t0
    assert r.status_code == 200, f"preview failed: {r.status_code} {r.text}"
    assert dt < 12.0, f"preview too slow: {dt:.2f}s"

    j = r.json()
    claims = j.get("claims")
    assert isinstance(claims, list) and len(claims) > 0, "claims missing/empty"
    c0 = claims[0]

    evidence = (c0 or {}).get("evidence") or {}
    armA = evidence.get("arm_A") or []
    armB = evidence.get("arm_B") or []
    assert isinstance(armA, list) and isinstance(armB, list) and armA and armB, "evidence arms missing/empty"

    # Verdict presence and shape
    verdict = (c0 or {}).get("verdict")
    assert isinstance(verdict, dict), "verdict missing"

    label_raw = verdict.get("label")
    assert isinstance(label_raw, str) and label_raw.strip(), "verdict.label missing"
    label = label_raw.strip().lower()
    assert label in ALLOWED_LABELS, f"invalid verdict.label: {label_raw}"

    conf = verdict.get("confidence")
    assert isinstance(conf, (int, float)), "verdict.confidence missing"
    conf = float(conf)
    assert 0.0 <= conf <= 1.0, "verdict.confidence out of range [0,1]"

    # Rationale references must map to evidence when label is not Insufficient
    refs = _extract_refs(verdict)
    if label != "insufficient":
        assert isinstance(refs, list) and len(refs) > 0, "verdict.rationale_refs missing"
        a_refs, b_refs = _refs_map_to_evidence(refs, armA, armB)
        assert (a_refs + b_refs) > 0, "rationale_refs do not map to evidence"
        if label == "support":
            assert a_refs > 0, "support label but no A-side refs"
        elif label == "challenge":
            assert b_refs > 0, "challenge label but no B-side refs"
        elif label == "mixed":
            assert a_refs > 0 and b_refs > 0, "mixed label but refs not from both arms"

    # Neutral consistency heuristic (non-binding but sanity): top-k score compare vs label
    sumA = _score_sum(armA, k=3)
    sumB = _score_sum(armB, k=3)
    diff = sumA - sumB
    if label == "support":
        assert diff >= -0.10, f"support label contradicts scores: A-B={diff:.3f}"
    elif label == "challenge":
        assert diff <= 0.10, f"challenge label contradicts scores: A-B={diff:.3f}"
    elif label == "mixed":
        assert abs(diff) <= 0.40, f"mixed label inconsistent with scores: A-B={diff:.3f}"
    else:  # insufficient
        pass

    # Output a compact verdict view
    sample = {
        "label": label_raw,
        "confidence": conf,
        "refs": list(map(lambda x: x if isinstance(x, (str,int)) else x.get("url"), refs))[:4]
    }
    print("P16 VERDICT:", json.dumps(sample))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"PACKET FAIL P16: {e}")
        sys.exit(1)
    print("PACKET PASS P16")
    sys.exit(0)
