from fastapi import FastAPI
from api.health import router as health_router
from api.analyses import router as analyses_router
from api.auth import router as auth_router
from api.secure_health import router as secure_router
app = FastAPI(title="ROGR API", version="1.0")
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(analyses_router)
app.include_router(secure_router)