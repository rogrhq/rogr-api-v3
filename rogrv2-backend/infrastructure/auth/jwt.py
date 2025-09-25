import os, time, jwt
from typing import Dict, Any, Optional
_SECRET = os.environ.get("AUTH_JWT_SECRET", "dev-secret-change-me")
_ALG = "HS256"
_ACCESS_TTL = int(os.environ.get("AUTH_ACCESS_TTL_SECONDS", "900"))
_REFRESH_TTL = int(os.environ.get("AUTH_REFRESH_TTL_SECONDS", "1209600"))
def create_access_token(sub: str, claims: Optional[Dict[str, Any]] = None) -> str:
    now = int(time.time())
    payload = {"sub": sub, "iat": now, "exp": now + _ACCESS_TTL}
    if claims: payload.update(claims)
    return jwt.encode(payload, _SECRET, algorithm=_ALG)
def create_refresh_token(sub: str) -> str:
    now = int(time.time())
    payload = {"sub": sub, "iat": now, "exp": now + _REFRESH_TTL, "typ": "refresh"}
    return jwt.encode(payload, _SECRET, algorithm=_ALG)
def verify_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, _SECRET, algorithms=[_ALG])