from __future__ import annotations
import os, datetime
from typing import Iterable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_LOG_PATH = "cors_debug.log"

def _writeln(line: str) -> None:
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

class CORSDebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if os.getenv("CORS_DEBUG") not in ("1", "true", "TRUE", "yes", "YES"):
            return await call_next(request)
        ts = datetime.datetime.utcnow().isoformat() + "Z"
        origin = request.headers.get("origin")
        _writeln(f"[{ts}] {request.method} {request.url.path} Origin={origin!r}")
        response: Response = await call_next(request)
        # Log only CORS-relevant headers
        hdrs = {k: v for k, v in response.headers.items() if "access-control" in k.lower() or k.lower() == "vary"}
        _writeln(f"[{ts}] -> status={response.status_code} headers={hdrs}")
        return response