#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from collections import Counter
from fastapi.testclient import TestClient

# --- Ensure repo root CWD and import path so `import main` resolves ---
REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(REPO_ROOT)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# --- Minimal .env loader (no external deps). Loads first existing: ---
# .env.local, .env.live, .env, config/.env, secrets/.env, .env.production
ENV_CANDIDATES = [
    ".env.local",
    ".env.live",
    ".env",
    "config/.env",
    "secrets/.env",
    ".env.production",
]

def _load_env():
    chosen = os.getenv("ENV_FILE")
    order = [chosen] if chosen else ENV_CANDIDATES
    for rel in order:
        if not rel:
            continue
        p = REPO_ROOT / rel
        if not p.is_file():
            continue
        try:
            with p.open("r", encoding="utf-8") as fh:
                for raw in fh:
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("export "):
                        line = line[len("export "):]
                    if "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and os.getenv(k) is None:
                        os.environ[k] = v
            return str(p)
        except Exception:
            continue
    return None

ENV_LOADED = _load_env()

# --- Canonical import target per OA: main:app ---
try:
    import main  # must exist at repo root
except Exception as e:
    raise RuntimeError("Cannot import main from repo root; ensure CWD is rogrv2-backend/ and sys.path includes it") from e

app = getattr(main, "app", None)
if app is None:
    raise RuntimeError("main.app not found; confirm FastAPI app object is defined in main.py")

# --- LIVE ONLY (no mocks). Accept env aliases (including your .env names) ---
ALIASES = {
    "brave": ["BRAVE_API_KEY", "BRAVE_KEY"],
    "google_api": ["GOOGLE_API_KEY", "GOOGLE_KEY", "GOOGLE_CSE_API_KEY"],
    "google_cse_id": ["GOOGLE_CSE_ID", "GOOGLE_CUSTOM_SEARCH_ENGINE_ID", "GOOGLE_CSE_ENGINE_ID"],
    "bing": ["BING_SUBSCRIPTION_KEY", "BING_API_KEY", "AZURE_BING_KEY"],
}

def _any(vars_list):
    return any(os.getenv(v) for v in vars_list)

def _providers_configured():
    brave = _any(ALIASES["brave"])
    google = _any(ALIASES["google_api"]) and _any(ALIASES["google_cse_id"])
    bing = _any(ALIASES["bing"])
    return brave, google, bing

brave_on, google_on, bing_on = _providers_configured()
if not (brave_on or google_on or bing_on):
    lines = [
        "Missing live provider configuration (checked process env and optional .env file). Set at least one provider:",
        "- Brave: BRAVE_API_KEY or BRAVE_KEY",
        "- Google CSE: GOOGLE_CSE_ID (or GOOGLE_CUSTOM_SEARCH_ENGINE_ID or GOOGLE_CSE_ENGINE_ID) AND "
        "GOOGLE_API_KEY (or GOOGLE_KEY or GOOGLE_CSE_API_KEY)",
        "- Bing: BING_SUBSCRIPTION_KEY or BING_API_KEY or AZURE_BING_KEY",
    ]
    if ENV_LOADED:
        lines.append(f"Loaded env from: {ENV_LOADED}")
    sys.stderr.write("\n".join(lines) + "\n")
    sys.exit(2)

client = TestClient(app)

# --- Auth flow verification ---
unauth = client.post("/analyses/preview", json={"text": "auth check", "test_mode": False})
assert unauth.status_code in (401, 403), f"Expected 401/403 unauth, got {unauth.status_code}"

reg = client.post("/auth/register", json={"email": "p14-live@rogr.app"}, headers={"Content-Type": "application/json"})
assert reg.status_code == 200, f"/auth/register failed: {reg.status_code} {reg.text}"
tok = (reg.json() or {}).get("access_token")
assert tok, "/auth/register did not return access_token"
headers = {"Authorization": f"Bearer {tok}"}

# --- LIVE call (no test mode) ---
r2 = client.post(
    "/analyses/preview",
    json={"text": "Austin increased its 2024 city budget by 8%.", "test_mode": False},
    headers=headers,
)
assert r2.status_code == 200, f"/analyses/preview failed: {r2.status_code} {r2.text}"
data = r2.json()

# Basic invariants
assert isinstance(data.get("claims"), list) and len(data["claims"]) >= 1, "no claims extracted"
c0 = data["claims"][0]
ev = c0.get("evidence") or {}
armA = ev.get("arm_A") or []
armB = ev.get("arm_B") or []

# Both arms must be non-empty
assert isinstance(armA, list) and len(armA) > 0, "arm_A empty"
assert isinstance(armB, list) and len(armB) > 0, "arm_B empty"

# Evidence items must preserve 'arm' and 'provider'
def _check_items(items):
    for i, it in enumerate(items):
        assert isinstance(it, dict), f"evidence[{i}] not dict"
        assert it.get("arm") in ("A", "B"), f"evidence[{i}] missing/invalid arm"
        assert isinstance(it.get("provider"), str) and it.get("provider"), f"evidence[{i}] missing provider"

_check_items(armA)
_check_items(armB)

# Provider usage surface
provs = [it.get("provider") for it in (armA + armB) if isinstance(it, dict) and it.get("provider")]
if provs:
    counts = Counter([p for p in provs if isinstance(p, str)])
    print("PROVIDERS:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))

print("PACKET PASS P14")
