import os
import sys
import time
import json
from typing import Dict, Any, List
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure we can import the FastAPI app regardless of CWD by adding the repo root
_HERE = Path(__file__).resolve()
_ROOT = _HERE.parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Import FastAPI app
import importlib
m = importlib.import_module("main")
assert hasattr(m, "app"), "main.app missing"
app = m.app
client = TestClient(app)

# Turn on diagnostics for this run (doesn't alter behavior)
os.environ.setdefault("ROGR_DIAG", "1")

CLAIM_TEXT_1 = "Austin increased its 2024 city budget by 8%."
CLAIM_TEXT_2 = "Austin's 2024 city budget did not increase by 8%."

ALLOWED_PROVIDERS = {"brave", "google", "bing"}


def enabled_providers() -> Dict[str, bool]:
    return {
        "brave": bool(os.getenv("BRAVE_API_KEY") or os.getenv("BRAVE_KEY")),
        "google": bool(
            (os.getenv("GOOGLE_CSE_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_KEY"))
            and (os.getenv("GOOGLE_CSE_ENGINE_ID") or os.getenv("GOOGLE_CSE_ID") or os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID"))
        ),
        "bing": bool(os.getenv("BING_SUBSCRIPTION_KEY") or os.getenv("BING_API_KEY") or os.getenv("AZURE_BING_KEY")),
    }


def get_token() -> str:
    # Use valid domain and uniqueness per run
    email = f"p14.strict.{int(time.time()*1000)}@example.com"
    r = client.post("/auth/register", json={"email": email})
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text} (email={email})"
    j = r.json()
    token = j.get("access_token") or j.get("token")
    assert token, f"no token in register response: {j}"
    return token


def preview(claim_text: str, token: str = None):
    body = {"text": claim_text}
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.post("/analyses/preview", json=body, headers=headers)


def assert_evidence_bundle(bundle: Dict[str, Any]) -> None:
    assert isinstance(bundle, dict), "evidence bundle must be dict"

    # Explicit keys are required (P14 contract)
    assert "arm_A" in bundle and "arm_B" in bundle, "missing arm_A/arm_B keys"

    armA = bundle.get("arm_A")
    armB = bundle.get("arm_B")
    assert isinstance(armA, list) and len(armA) > 0, "arm_A empty"
    assert isinstance(armB, list) and len(armB) > 0, "arm_B empty"

    # If legacy keys are present, they must mirror explicit keys
    if ("A" in bundle) or ("B" in bundle):
        assert "A" in bundle and "B" in bundle, "legacy keys must appear together"
        assert bundle["A"] == armA, "legacy A must equal arm_A"
        assert bundle["B"] == armB, "legacy B must equal arm_B"

    # Evidence shape and bias checks (no content-quality gating in P14)
    for arm_list in (armA, armB):
        for it in arm_list:
            assert isinstance(it, dict), "evidence item must be dict"
            assert it.get("url"), "missing url"
            assert it.get("title") is not None, "missing title"
            assert it.get("snippet") is not None, "missing snippet"
            assert it.get("provider") in ALLOWED_PROVIDERS, f"bad provider {it.get('provider')}"
            assert it.get("arm") in {"A", "B"}, f"bad arm {it.get('arm')}"
            qeff = it.get("q_effective", "")
            assert '"' not in (qeff or ''), f"q_effective contains quotes: {qeff!r}"
            qeff_l = (qeff or '').lower()
            assert "site:" not in qeff_l, f"q_effective must not contain site: {qeff!r}"

    # Provider diversity when multiple providers are live
    enabled = enabled_providers()
    live_enabled = [p for p, v in enabled.items() if v]
    provs = {it.get("provider") for it in (armA + armB) if it.get("provider") in ALLOWED_PROVIDERS}
    if len(live_enabled) >= 2:
        assert len(provs) >= 2, f"provider diversity failed; enabled={live_enabled}, got={sorted(provs)}"


def main() -> None:
    # 401 check
    r401 = preview(CLAIM_TEXT_1, token=None)
    assert r401.status_code in (401, 403), f"expected 401/403 without token, got {r401.status_code}"

    # Auth
    token = get_token()

    # Timed preview
    t0 = time.monotonic()
    r = preview(CLAIM_TEXT_1, token=token)
    dt = time.monotonic() - t0
    assert r.status_code == 200, f"preview failed: {r.status_code} {r.text}"
    assert dt < 12.0, f"preview too slow: {dt:.2f}s"
    j = r.json()
    claims = j.get("claims")
    assert isinstance(claims, list) and len(claims) > 0, "claims missing/empty"
    evidence = (claims[0] or {}).get("evidence") or {}
    assert_evidence_bundle(evidence)

    # Second claim to exercise multi-claim readiness (sequentially)
    r2 = preview(CLAIM_TEXT_2, token=token)
    assert r2.status_code == 200, f"second preview failed: {r2.status_code} {r2.text}"
    j2 = r2.json() or {}
    claims2 = j2.get("claims")
    assert isinstance(claims2, list) and len(claims2) > 0, "claims missing/empty (second)"
    evidence2 = (claims2[0] or {}).get("evidence") or {}
    assert_evidence_bundle(evidence2)

    # Print provider counts and sample evidence for visibility (non-blocking)
    prov_counts: Dict[str, int] = {}
    for it in (evidence.get("arm_A", []) + evidence.get("arm_B", [])):
        p = it.get("provider")
        prov_counts[p] = prov_counts.get(p, 0) + 1
    pc_line = ", ".join(f"{k}={v}" for k, v in sorted(prov_counts.items()))
    print(f"P14-STRICT PROVIDERS: {pc_line}")

    # Sample titles/snippets (first 2 per arm) for human visibility (non-blocking)
    def _sample(arm_list: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        out = []
        for it in arm_list[:2]:
            out.append({"provider": it.get("provider"), "title": it.get("title"), "snippet": it.get("snippet")})
        return out

    print("P14-STRICT SAMPLE arm_A:", json.dumps(_sample(evidence.get("arm_A", [])), ensure_ascii=False)[:800])
    print("P14-STRICT SAMPLE arm_B:", json.dumps(_sample(evidence.get("arm_B", [])), ensure_ascii=False)[:800])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"P14-STRICT FAIL: {e}")
        sys.exit(1)
    print("PACKET PASS P14-STRICT")
    sys.exit(0)
