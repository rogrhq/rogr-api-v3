from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from infrastructure.auth.jwt import verify_token

bearer = HTTPBearer()

def require_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    try:
        payload = verify_token(creds.credentials)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")