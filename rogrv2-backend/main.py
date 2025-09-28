from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from infrastructure.http.security import EnforceJsonAndSizeMiddleware
from infrastructure.http.context import RequestContextMiddleware
from infrastructure.http.errors import install_handlers
import os
from workers import queue as _job_queue
from api.health import router as health_router
from api.analyses import router as analyses_router
from api.auth import router as auth_router
from api.secure_health import router as secure_router
from api.auth_me import router as auth_me_router
from api.analyses_commit import router as commit_router
from api.analyses_read import router as analyses_read_router
from api.contracts import router as contracts_router
from api.mobile import router as mobile_router
from api.ifcn_export import router as ifcn_export_router
from api.ops import router as ops_router
from api.profile import router as profile_router
from api.media import router as media_router
from api.notifications import router as notifications_router
from api.admin import router as admin_router
from api.jobs import router as jobs_router
from api.metrics import router as metrics_router
from infrastructure.metrics import install_http_middleware
from infrastructure.logging.jtrace import error_event, format_exc

# CORS configuration (deterministic; outermost middleware)
_cors_env = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://testserver,http://localhost,http://127.0.0.1,http://localhost:19006,http://localhost:3000",
)
_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]
_allow_regex = os.getenv("CORS_ALLOWED_ORIGIN_REGEX", r"^https?://(localhost|127\.0\.0\.1|testserver)(:\d+)?$")
_middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_origin_regex=_allow_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = FastAPI(title="ROGR API", version="1.0", middleware=_middleware)
install_http_middleware(app)

# Add JSON & request-size enforcement middleware
app.add_middleware(EnforceJsonAndSizeMiddleware)
# Add request-id propagation middleware (must run early)
app.add_middleware(RequestContextMiddleware)
# Install unified error handlers (after app instantiated)
install_handlers(app)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(analyses_router)
app.include_router(secure_router)

# Dev-only: return richer error body when ROGR_DEBUG_ERRORS=1
if os.getenv("ROGR_DEBUG_ERRORS") == "1":
    @app.middleware("http")
    async def debug_errors(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            rid = error_event("unhandled_exception", path=request.url.path, detail=str(e), traceback=format_exc(e))
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={"error":"server_error","detail":str(e),"request_id":rid,"debug":"trace logged"},
            )
app.include_router(auth_me_router)
app.include_router(commit_router)
app.include_router(analyses_read_router)
app.include_router(contracts_router)
app.include_router(mobile_router)
app.include_router(ifcn_export_router)
app.include_router(ops_router)
app.include_router(profile_router)
app.include_router(media_router)
app.include_router(notifications_router)
app.include_router(admin_router)
app.include_router(jobs_router)
app.include_router(metrics_router)
app.include_router(contracts_router)

@app.on_event("startup")
def _start_workers():
    # Ensure the in-proc job queue is started once per process
    _job_queue.start()

# (Debug middleware removed for production-clean baseline)