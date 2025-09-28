from __future__ import annotations
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
from typing import Optional

JSON_CT_PREFIXES = ("application/json", "application/",)  # allow application/json and application/*+json

def _is_json(ct: Optional[str]) -> bool:
    if not ct:
        return False
    ct = ct.split(";")[0].strip().lower()
    if ct == "application/json":
        return True
    # application/*+json (e.g., application/ld+json)
    if ct.startswith("application/") and ct.endswith("+json"):
        return True
    return False

class EnforceJsonAndSizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, max_bytes: int = 1_048_576) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        # Only enforce for methods that carry bodies
        if request.method.upper() not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        ct = request.headers.get("content-type", "")
        # Always buffer body so we can safely pass it downstream
        try:
            body = await request.body()
        except Exception:
            body = b""

        # Size check (applies to all)
        if len(body) > self.max_bytes:
            return PlainTextResponse("payload too large", status_code=413)

        # If it's JSON, enforce that it is present and valid type header
        if _is_json(ct):
            # Re-inject the buffered body so downstream can read it
            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}
            request._receive = receive  # type: ignore[attr-defined]
            return await call_next(request)

        # Not JSON: leave as-is and pass through (your routes can still reject with 415)
        async def receive_passthrough():
            return {"type": "http.request", "body": body, "more_body": False}
        request._receive = receive_passthrough  # type: ignore[attr-defined]
        return await call_next(request)