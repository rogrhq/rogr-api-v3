from __future__ import annotations
from typing import Any, Dict
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from infrastructure.logging.ctx import get_request_id

def _envelope(kind: str, status: int, detail: Any) -> Dict[str, Any]:
    rid = get_request_id()
    return {"error": kind, "status": status, "detail": detail, "request_id": rid}

def install_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def _http_exc_handler(request: Request, exc: StarletteHTTPException):
        # detail may be str or dict; keep as-is
        return JSONResponse(status_code=exc.status_code, content=_envelope("http_error", exc.status_code, exc.detail))

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content=_envelope("validation_error", 422, exc.errors()))

    @app.exception_handler(Exception)
    async def _uncaught(request: Request, exc: Exception):
        # avoid leaking internals; return minimal message
        return JSONResponse(status_code=500, content=_envelope("server_error", 500, "internal server error"))