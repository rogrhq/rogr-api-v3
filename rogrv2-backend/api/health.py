from fastapi import APIRouter
router = APIRouter()
@router.get("/health/db")
def db_health():
    return {"status": "ok"}