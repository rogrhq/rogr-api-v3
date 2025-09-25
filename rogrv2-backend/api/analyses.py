from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from infrastructure.auth.deps import require_user
from intelligence.pipeline.run import run_preview

router = APIRouter(prefix="/analyses", tags=["analyses"])

class PreviewBody(BaseModel):
    text: str
    test_mode: bool = True

class EvidenceOut(BaseModel):
    stance: str
    confidence: float
    quality_letter: str
    source: Dict[str, Any]

class ClaimOut(BaseModel):
    text: str
    tier: str
    priority: int
    strategies: Dict[str, list]
    evidence: Dict[str, list]     # lists of EvidenceOut; keep as plain list for now
    consensus: Dict[str, Any]
    score_numeric: int
    label: str
    explanation: str

class PreviewOut(BaseModel):
    claims: list
    overall: Dict[str, Any]

@router.post("/preview", response_model=PreviewOut)
def preview(body: PreviewBody, _user=Depends(require_user)):
    data = run_preview(body.text, test_mode=body.test_mode)
    return data