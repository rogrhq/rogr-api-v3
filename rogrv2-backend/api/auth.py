from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
from infrastructure.auth.jwt import create_access_token, create_refresh_token, verify_token

router = APIRouter()

class RegisterBody(BaseModel):
    email: EmailStr

@router.post("/auth/register")
def register(body: RegisterBody):
    user_id = body.email.lower()  # MVP: use email as subject
    return {
        "access_token": create_access_token(user_id, {"role":"user"}),
        "refresh_token": create_refresh_token(user_id)
    }

class RefreshBody(BaseModel):
    refresh_token: str

@router.post("/auth/refresh")
def refresh(body: RefreshBody):
    payload = verify_token(body.refresh_token)
    if payload.get("typ") != "refresh":
        return {"error":"invalid token"}
    user_id = payload["sub"]
    return {"access_token": create_access_token(user_id, {"role":"user"})}