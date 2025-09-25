from __future__ import annotations
from fastapi import APIRouter, Depends
from infrastructure.auth.deps import require_user
from infrastructure.http.limits import rate_limit_dep

router = APIRouter()

@router.get("/auth/me")
def auth_me(_rl=Depends(rate_limit_dep), user=Depends(require_user)):
    # Minimal, deterministic shape; subject comes from JWT 'sub'
    sub = user.get("sub", "user@example.com")
    role = user.get("role", "user")
    return {"sub": sub, "roles": [role], "exp": user.get("exp", 0)}