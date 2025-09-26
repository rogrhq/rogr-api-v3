from __future__ import annotations
from typing import Callable, Iterable, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
import os

def _parse_origins(env_val: str | None) -> List[str]:
    if not env_val:
        return []
    return [o.strip() for o in env_val.split(",") if o.strip()]

class ForceCORSMiddleware(BaseHTTPMiddleware):
    """
    Deterministic CORS headers for tests/clients that don't trigger Starlette's CORS logic.
    Adds ACAO/ACAC and handles OPTIONS preflight when Origin matches allowlist.
    """
    def __init__(self, app, allow_origins: Iterable[str], allow_credentials: bool = True):
        super().__init__(app)
        self.allow = list(allow_origins)
        self.allow_credentials = allow_credentials

    async def dispatch(self, request: Request, call_next: Callable):
        origin = request.headers.get("origin")
        # Only act if we have an Origin header and it's allowed
        if origin and (origin in self.allow or "*" in self.allow):
            # Handle preflight early
            if request.method.upper() == "OPTIONS" and request.headers.get("access-control-request-method"):
                headers = {
                    "Access-Control-Allow-Origin": origin if origin in self.allow else "*",
                    "Vary": "Origin",
                    "Access-Control-Allow-Methods": request.headers.get("access-control-request-method", "*"),
                    "Access-Control-Allow-Headers": request.headers.get("access-control-request-headers", "*"),
                }
                if self.allow_credentials:
                    headers["Access-Control-Allow-Credentials"] = "true"
                return PlainTextResponse("", status_code=204, headers=headers)

            # Normal request path
            response: Response = await call_next(request)
            response.headers["Access-Control-Allow-Origin"] = origin if origin in self.allow else "*"
            response.headers["Vary"] = "Origin"
            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"
            return response

        # No origin or not allowed: pass through
        return await call_next(request)