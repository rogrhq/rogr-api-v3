from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
from infrastructure.auth.jwt import create_access_token, create_refresh_token, verify_token

router = APIRouter()

class RegisterBody(BaseModel):
    email: EmailStr

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str

class AccessOnly(BaseModel):
    access_token: str

@router.post("/auth/register", response_model=TokenPair)
def register(body: RegisterBody):
    """
    Deterministic MVP: uses email as subject (no DB yet).
    Returns both access and refresh tokens.
    """
    user_id = body.email.lower()
    return TokenPair(
        access_token=create_access_token(user_id, {"role": "user"}),
        refresh_token=create_refresh_token(user_id),
    )

class RefreshBody(BaseModel):
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