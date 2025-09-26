from __future__ import annotations
import os, sys
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from database.session import engine
from infrastructure.auth.deps import require_user
from infrastructure.http.limits import rate_limit_dep

router = APIRouter()

def _mask(val: str | None) -> str | None:
    if val is None:
        return None
    v = str(val)
    if len(v) <= 4:
        return "***"
    return "***" + v[-4:]

@router.get("/version")
def version() -> Dict[str, Any]:
    name = os.getenv("APP_NAME", "ROGR API")
    version = os.getenv("APP_VERSION", "1.0")
    build = os.getenv("GIT_SHA", "")[:12]
    py = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return {"name": name, "version": version, "build": build, "python": py}

@router.get("/health/ready")
async def health_ready() -> Dict[str, Any]:
    ok_db = False
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        ok_db = True
    except Exception:
        ok_db = False
    return {"ready": bool(ok_db), "checks": {"db": bool(ok_db)}}

@router.get("/ops/env")
def env_view(
    keys: str = Query("", description="comma-separated env keys to view (masked)"),
    _rl=Depends(rate_limit_dep),
    _user=Depends(require_user),
) -> Dict[str, Any]:
    wanted: List[str] = [k.strip() for k in (keys or "").split(",") if k.strip()]
    out: Dict[str, Any] = {}
    for k in wanted:
        out[k] = _mask(os.getenv(k))
    return {"env": out}