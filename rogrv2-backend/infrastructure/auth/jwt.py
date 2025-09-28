import os, time, jwt
from typing import Dict, Any, Optional
# Use a stable default secret for local/dev to avoid mismatches when env is missing
SECRET = os.environ.get("AUTH_JWT_SECRET", "dev-secret")
_ALG = "HS256"
_ACCESS_TTL = int(os.environ.get("AUTH_ACCESS_TTL_SECONDS", "900"))
_REFRESH_TTL = int(os.environ.get("AUTH_REFRESH_TTL_SECONDS", "1209600"))
def create_access_token(sub: str, claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Access tokens now explicitly include typ='access' for robust verification.
    """
    now = int(time.time())
    payload = {"sub": sub, "iat": now, "exp": now + _ACCESS_TTL, "typ": "access"}
    if claims: payload.update(claims)
    return jwt.encode(payload, SECRET, algorithm=_ALG)
def create_refresh_token(sub: str) -> str:
    now = int(time.time())
    payload = {"sub": sub, "iat": now, "exp": now + _REFRESH_TTL, "typ": "refresh"}
    return jwt.encode(payload, SECRET, algorithm=_ALG)

# Backward/forgiving verification: accepts tokens with/without 'typ'
def verify_token(token: str) -> dict:
    """
    Decode JWT with small leeway to avoid clock skew, and default typ to 'access'
    if missing (older tokens).
    """
    payload = jwt.decode(token, SECRET, algorithms=["HS256"], options={"require": ["exp", "sub"]}, leeway=5)
    if "typ" not in payload:
        payload["typ"] = "access"
    return payload