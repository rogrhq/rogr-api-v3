from fastapi import APIRouter, Depends
from pydantic import BaseModel
from infrastructure.auth.deps import require_user

router = APIRouter(prefix="/analyses", tags=["analyses"])

class HealthResp(BaseModel):
    ok: bool

@router.get("/healthcheck", response_model=HealthResp)
def check(_user=Depends(require_user)):
    # If auth fails, require_user raises HTTPException and this never runs
    return {"ok": True}