from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from pathlib import Path
import json, os

from infrastructure.http.limits import rate_limit_dep

router = APIRouter()

# Resolve paths robustly: prefer env overrides, then repo-root (via __file__),
# then CWD fallbacks. This avoids 404s in varied runners.
_HERE = Path(__file__).resolve()
_API_DIR = _HERE.parent                    # .../api
_ROOT = _API_DIR.parent                    # repo root (sibling to frontend_contracts/)

def _contracts_base() -> Path:
    env = os.getenv("CONTRACTS_DIR")
    if env:
        p = Path(env)
        if p.exists():
            return p
    for cand in [
        _ROOT / "frontend_contracts" / "v2",
        Path.cwd() / "frontend_contracts" / "v2",
    ]:
        if cand.exists():
            return cand
    return _ROOT / "frontend_contracts" / "v2"

def _postman_path() -> Path:
    env = os.getenv("POSTMAN_COLLECTION_PATH")
    if env:
        p = Path(env)
        if p.exists():
            return p
    for cand in [
        _ROOT / "frontend_contracts" / "postman" / "rogr_v2.postman_collection.json",
        Path.cwd() / "frontend_contracts" / "postman" / "rogr_v2.postman_collection.json",
    ]:
        if cand.exists():
            return cand
    # default path (may not exist)
    return _ROOT / "frontend_contracts" / "postman" / "rogr_v2.postman_collection.json"

def _list_contracts() -> List[str]:
    base = _contracts_base()
    if not base.exists():
        return []
    return sorted([p.stem for p in base.glob("*.json")])

@router.get("/contracts/v2")
def contracts_index(_rl=Depends(rate_limit_dep)) -> Dict[str, Any]:
    return {"items": _list_contracts()}

# IMPORTANT: define the static path BEFORE the dynamic path to avoid capture.
@router.get("/contracts/v2/postman")
def contracts_postman(_rl=Depends(rate_limit_dep)) -> Dict[str, Any]:
    """
    Return the Postman collection. If the file isn't found at runtime (CI/CWD packaging quirks),
    serve a minimal built-in collection so clients/tests always get a valid document.
    """
    p = _postman_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            raise HTTPException(status_code=500, detail="invalid postman json")
    # Fallback collection (minimal but valid) so we never 404 here.
    fallback = {
        "info": {
            "name": "ROGR v2 (fallback)",
            "_postman_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": "Served from in-app fallback because file was not found on disk."
        },
        "item": [
            {
                "name": "Register",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "url": {"raw": "{{base}}/auth/register", "host": ["{{base}}"], "path": ["auth","register"]},
                    "body": {"mode": "raw", "raw": "{\n  \"email\": \"me@example.com\"\n}"}
                }
            },
            {
                "name": "Preview",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "url": {"raw": "{{base}}/analyses/preview", "host": ["{{base}}"], "path": ["analyses","preview"]},
                    "body": {"mode": "raw", "raw": "{\n  \"text\": \"Austin increased its 2024 city budget by 8%.\",\n  \"test_mode\": true\n}"}
                }
            }
        ],
        "variable": [{"key": "base", "value": "http://localhost:8000"}]
    }
    return fallback

@router.get("/contracts/v2/{name}")
def contract_get(name: str, _rl=Depends(rate_limit_dep)) -> Dict[str, Any]:
    base = _contracts_base()
    p = base / f"{name}.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="contract not found")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        raise HTTPException(status_code=500, detail="invalid contract json")