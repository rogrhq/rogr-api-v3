from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from infrastructure.http.cors_force import ForceCORSMiddleware
from workers import queue as _job_queue
from api.health import router as health_router
from api.analyses import router as analyses_router
from api.auth import router as auth_router
from api.secure_health import router as secure_router
from api.auth_me import router as auth_me_router
from api.feed import router as feed_router
from api.archive import router as archive_router
from api.analyses_read import router as analyses_read_router
from api.contracts import router as contracts_router
from api.jobs import router as jobs_router
app = FastAPI(title="ROGR API", version="1.0")

# CORS: allow mobile/web dev origins; credentials enabled for Authorization header scenarios
_cors_env = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:19006,http://localhost:3000")
_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,          # explicit list (no "*" when credentials are allowed)
    allow_credentials=True,          # enables credentialed requests (Authorization/cookies)
    allow_methods=["*"],
    allow_headers=["*"],
)
# Add a forcing layer so responses *always* carry ACAO when Origin matches, and OPTIONS preflight succeeds.
app.add_middleware(ForceCORSMiddleware, allow_origins=_origins, allow_credentials=True)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(analyses_router)
app.include_router(secure_router)
app.include_router(auth_me_router)
app.include_router(feed_router)
app.include_router(archive_router)
app.include_router(analyses_read_router)
app.include_router(contracts_router)
app.include_router(jobs_router)

@app.on_event("startup")
def _start_workers():
    # Ensure the in-proc job queue is started once per process
    _job_queue.start()