from __future__ import annotations
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from infrastructure.logging.ctx import set_request_id

_HEADER = "x-request-id"

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get(_HEADER)
        if not rid:
            rid = str(uuid.uuid4())
        # set into context for downstream and logs
        set_request_id(rid)
        response: Response = await call_next(request)
        response.headers[_HEADER] = rid
        return response