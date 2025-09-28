from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from infrastructure.auth.jwt import verify_token
from infrastructure.auth.freeze import is_frozen

bearer = HTTPBearer(auto_error=False)

def require_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if not creds:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        payload = verify_token(creds.credentials)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")

def require_admin(user: dict = Depends(require_user)) -> dict:
    if user.get("role") == "admin":
        return user
    raise HTTPException(status_code=403, detail="Forbidden: admin required")