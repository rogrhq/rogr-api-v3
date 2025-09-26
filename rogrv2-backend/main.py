from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from infrastructure.http.security import EnforceJsonAndSizeMiddleware
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
from api.jobs import router as jobs_router

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

# Add JSON & request-size enforcement middleware
app.add_middleware(EnforceJsonAndSizeMiddleware)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(analyses_router)
app.include_router(secure_router)
app.include_router(auth_me_router)
app.include_router(commit_router)
app.include_router(analyses_read_router)
app.include_router(contracts_router)
app.include_router(mobile_router)
app.include_router(jobs_router)

@app.on_event("startup")
def _start_workers():
    # Ensure the in-proc job queue is started once per process
    _job_queue.start()

# (Debug middleware removed for production-clean baseline)