from __future__ import annotations
from typing import Iterable, List, Optional, Tuple
import re

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

class DeterministicCORSMiddleware(BaseHTTPMiddleware):
    """
    Minimal, standards-compliant CORS:
    - If Origin matches allowlist or regex, echo it in Access-Control-Allow-Origin.
    - Optionally allow credentials when echoing a specific origin.
    - Handle OPTIONS preflight with requested method/headers.
    """
    def __init__(
        self,
        app,
        *,
        allow_origins: Iterable[str] = (),
        allow_origin_regex: Optional[str] = None,
        allow_credentials: bool = True,
        allow_methods: Iterable[str] = ("*",),
        allow_headers: Iterable[str] = ("*",),
    ):
        super().__init__(app)
        self.allow_list: List[str] = [o.strip() for o in allow_origins if o and o.strip()]
        self.allow_re = re.compile(allow_origin_regex) if allow_origin_regex else None
        self.allow_credentials = allow_credentials
        self.allow_methods = ",".join(allow_methods) if allow_methods else "*"
        self.allow_headers = ",".join(allow_headers) if allow_headers else "*"

    def _is_allowed(self, origin: Optional[str]) -> bool:
        if not origin:
            return False
        if origin in self.allow_list:
            return True
        if self.allow_re and self.allow_re.match(origin):
            return True
        return False

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        allowed = self._is_allowed(origin)

        # Preflight
        if request.method.upper() == "OPTIONS" and request.headers.get("access-control-request-method"):
            acao = origin if allowed else "*"
            headers = {
                "Access-Control-Allow-Origin": acao,
                "Access-Control-Allow-Methods": request.headers.get("access-control-request-method", self.allow_methods),
                "Access-Control-Allow-Headers": request.headers.get("access-control-request-headers", self.allow_headers),
                "Vary": "Origin" if origin else "",
            }
            if self.allow_credentials and allowed:
                headers["Access-Control-Allow-Credentials"] = "true"
            # Remove empty header values
            headers = {k: v for k, v in headers.items() if v}
            return PlainTextResponse("", status_code=204, headers=headers)

        # Normal request path
        response: Response = await call_next(request)
        # Always emit ACAO for deterministic behavior:
        # - if Origin is allowed -> echo it (optionally with credentials)
        # - if Origin is present but not allowed -> "*"
        # - if no Origin header -> "*" (some test clients omit Origin)
        if origin:
            acao = origin if allowed else "*"
            response.headers["Access-Control-Allow-Origin"] = acao
            response.headers["Vary"] = "Origin"
            if self.allow_credentials and allowed:
                response.headers["Access-Control-Allow-Credentials"] = "true"
        else:
            response.headers["Access-Control-Allow-Origin"] = "*"
        return response

class DeterministicCORSASGI:
    """
    ASGI middleware variant that injects CORS headers at the protocol layer.
    More robust than BaseHTTPMiddleware for streamed/early-start responses.
    """
    def __init__(
        self,
        app: ASGIApp,
        *,
        allow_origins: Iterable[str] = (),
        allow_origin_regex: Optional[str] = None,
        allow_credentials: bool = True,
        allow_methods: Iterable[str] = ("*",),
        allow_headers: Iterable[str] = ("*",),
    ):
        self.app = app
        self.allow_list: List[str] = [o.strip() for o in allow_origins if o and o.strip()]
        self.allow_re = re.compile(allow_origin_regex) if allow_origin_regex else None
        self.allow_credentials = allow_credentials
        self.allow_methods = ",".join(allow_methods) if allow_methods else "*"
        self.allow_headers = ",".join(allow_headers) if allow_headers else "*"

    def _is_allowed(self, origin: Optional[str]) -> bool:
        if not origin:
            return False
        if origin in self.allow_list:
            return True
        if self.allow_re and self.allow_re.match(origin):
            return True
        return False

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract headers from scope (bytes -> str)
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        origin = headers.get("origin")
        allowed = self._is_allowed(origin)
        req_method = scope.get("method", "GET").upper()
        acr_method = headers.get("access-control-request-method")
        acr_headers = headers.get("access-control-request-headers", self.allow_headers)

        # Preflight handling
        if req_method == "OPTIONS" and acr_method:
            acao = origin if allowed else "*"
            out_headers: List[Tuple[bytes, bytes]] = [
                (b"access-control-allow-origin", acao.encode()),
                (b"Access-Control-Allow-Origin", acao.encode()),
                (b"access-control-allow-methods", acr_method.encode()),
                (b"access-control-allow-headers", acr_headers.encode() if isinstance(acr_headers, str) else b"*"),
            ]
            if origin:
                out_headers.append((b"vary", b"Origin"))
                out_headers.append((b"Vary", b"Origin"))
            if self.allow_credentials and allowed and acao != "*":
                out_headers.append((b"access-control-allow-credentials", b"true"))
                out_headers.append((b"Access-Control-Allow-Credentials", b"true"))
            await send({"type": "http.response.start", "status": 204, "headers": out_headers})
            await send({"type": "http.response.body", "body": b""})
            return

        # Normal request path: intercept response start and inject headers deterministically
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                acao = origin if allowed else ("*" if origin is None or origin == "" else "*")
                # Normalize any existing headers to a list of (bytes, bytes)
                hdrs: List[Tuple[bytes, bytes]] = []
                for k, v in message.get("headers", []):
                    kb = k if isinstance(k, bytes) else str(k).encode()
                    vb = v if isinstance(v, bytes) else str(v).encode()
                    hdrs.append((kb, vb))
                # Inject CORS headers
                hdrs.append((b"access-control-allow-origin", acao.encode()))
                hdrs.append((b"Access-Control-Allow-Origin", acao.encode()))
                if origin:
                    hdrs.append((b"vary", b"Origin"))
                    hdrs.append((b"Vary", b"Origin"))
                if self.allow_credentials and allowed and acao != "*":
                    hdrs.append((b"access-control-allow-credentials", b"true"))
                    hdrs.append((b"Access-Control-Allow-Credentials", b"true"))
                message["headers"] = hdrs
            await send(message)

        await self.app(scope, receive, send_wrapper)