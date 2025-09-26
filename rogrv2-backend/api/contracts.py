from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import JSONResponse
from pathlib import Path
import json

from infrastructure.auth.deps import require_user
from infrastructure.http.limits import rate_limit_dep

router = APIRouter()

_BASE = Path(__file__).resolve().parents[1] / "frontend_contracts" / "v1"

@router.get("/contracts/v1/{name}")
def get_contract(name: str, _rl=Depends(rate_limit_dep), _user=Depends(require_user)):
    # Only allow .json within frontend_contracts/v1
    if not name.endswith(".json"):
        raise HTTPException(status_code=400, detail="contract must end with .json")
    p = (_BASE / name).resolve()
    if _BASE not in p.parents and _BASE != p.parent:
        raise HTTPException(status_code=400, detail="invalid path")
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="not found")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        raise HTTPException(status_code=500, detail="invalid json")
    return JSONResponse(data)