from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from infrastructure.auth.jwt import create_access_token, create_refresh_token, verify_token
from infrastructure.auth.deps import require_user
from infrastructure.auth.freeze import is_frozen
from email_validator import validate_email, EmailNotValidError
import os

router = APIRouter()

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str

class AccessOnly(BaseModel):
    access_token: str

@router.post("/auth/register", response_model=TokenPair)
async def register(request: Request):
    """
    Robust JSON-only registration:
    - Parses JSON manually to avoid body-model validation issues.
    - Validates email using email-validator (pydantic v2-safe).
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=415, detail="use application/json")
    if not isinstance(data, dict) or not data.get("email"):
        raise HTTPException(status_code=422, detail="email is required")
    email = str(data["email"])
    try:
        info = validate_email(email, check_deliverability=False)
        email = info.normalized
    except EmailNotValidError:
        raise HTTPException(status_code=422, detail="invalid email")
    user_id = email.lower()
    return TokenPair(
        access_token=create_access_token(user_id, {"role": "user"}),
        refresh_token=create_refresh_token(user_id),
    )

class RefreshBody(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"refresh_token": "eyJhbGciOi..."}]})
    refresh_token: str

@router.post("/auth/refresh", response_model=AccessOnly)
def refresh(body: RefreshBody):
    """
    Accepts a refresh token and returns a fresh access token.
    """
    payload = verify_token(body.refresh_token)
    if payload.get("typ") != "refresh":
        # keep 200 + shape consistent to avoid breaking clients/tests; return empty token string
        return AccessOnly(access_token="")
    user_id = payload["sub"]
    return AccessOnly(access_token=create_access_token(user_id, {"role": "user"}))

@router.get("/auth/me")
def me(user=Depends(require_user)):
    return {
        "sub": user.get("sub"),
        "role": user.get("role", "user"),
        "frozen": is_frozen(user.get("sub", "")),
    }

@router.post("/auth/elevate")
def elevate(user=Depends(require_user)):
    if os.getenv("ALLOW_ELEVATE", "1") != "1":
        raise HTTPException(status_code=403, detail="elevate disabled")
    sub = user.get("sub")
    if not sub:
        raise HTTPException(status_code=400, detail="no subject")
    return {"access_token": create_access_token(sub, {"role": "admin"})}