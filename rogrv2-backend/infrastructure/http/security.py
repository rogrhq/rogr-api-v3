from __future__ import annotations
from typing import Iterable, Tuple
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

_WRITE_PREFIXES: Tuple[str, ...] = (
    "/analyses", "/mobile", "/jobs", "/auth", "/contracts"  # safe set; JSON expected where POST used
)

def _max_body_bytes() -> int:
    try:
        return int(os.getenv("MAX_BODY_BYTES", "131072"))  # 128 KiB default
    except Exception:
        return 131072

class EnforceJsonAndSizeMiddleware(BaseHTTPMiddleware):
    """
    - For POST/PUT/PATCH under selected prefixes, require Content-Type: application/json (or +json).
    - Enforce a max body size for all requests (reads body into memory once, replays to downstream).
    Returns 415 for wrong media type, 413 for too large.
    """
    def __init__(self, app, write_prefixes: Iterable[str] = _WRITE_PREFIXES):
        super().__init__(app)
        self._prefixes = tuple(write_prefixes)

    async def dispatch(self, request: Request, call_next):
        # Enforce size
        body = await request.body()
        limit = _max_body_bytes()
        if len(body) > limit:
            return JSONResponse({"error": "request too large"}, status_code=413)

        # For write methods under our prefixes, enforce JSON content-type
        method = request.method.upper()
        if method in ("POST", "PUT", "PATCH") and request.url.path.startswith(self._prefixes):
            ctype = request.headers.get("content-type", "")
            if "application/json" not in ctype and "+json" not in ctype:
                return JSONResponse({"error": "unsupported media type; use application/json"}, status_code=415)

        # Re-inject the body for downstream (so handlers can read it)
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        request._receive = receive  # type: ignore[attr-defined]

        return await call_next(request)