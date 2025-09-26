from __future__ import annotations
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib

from infrastructure.auth.deps import require_user
from infrastructure.http.limits import rate_limit_dep
from infrastructure.storage import save_upload_bytes
from intelligence.extractors import extract_text
from database.session import Session
from database.models import MediaAsset, Analysis
from database.repo import save_analysis_with_claims, ensure_schema, persist_result_into_analysis

router = APIRouter()

class PreviewFromMediaBody(BaseModel):
    media_id: str
    test_mode: bool = True

class CommitFromMediaBody(BaseModel):
    media_id: str
    test_mode: bool = True

@router.post("/media/upload")
async def upload_media(
    kind: str = Form(..., description="text|image|audio|video"),
    file: UploadFile = File(...),
    analysis_id: Optional[str] = Form(None),
    _rl=Depends(rate_limit_dep),
    _user=Depends(require_user),
) -> Dict[str, Any]:
    await ensure_schema()
    data = await file.read()
    stored = save_upload_bytes(filename=file.filename or "upload.bin", data=data)
    # Extract text (deterministic stubs for non-text kinds)
    extracted = extract_text(kind, data, filename=file.filename or "", test_mode=True)
    # Attach to analysis or create one in 'uploaded' status
    async with Session() as s:  # type: AsyncSession
        if analysis_id:
            an = await s.get(Analysis, analysis_id)
            if not an:
                raise HTTPException(status_code=404, detail="analysis not found")
        else:
            an = Analysis(input_type=kind, original_uri=stored["path"], status="uploaded")
            s.add(an)
            await s.flush()
        ma = MediaAsset(
            analysis_id=an.id,
            kind=kind,
            storage_uri=stored["path"],
            checksum=stored["sha256"],
            extracted_text=extracted,
            language=None,
        )
        s.add(ma)
        await s.commit()
        return {
            "media_id": ma.id,
            "analysis_id": an.id,
            "kind": kind,
            "checksum": stored["sha256"],
            "extracted_text_len": len(extracted or ""),
        }

@router.post("/mobile/preview_from_media")
async def preview_from_media(
    body: PreviewFromMediaBody,
    _rl=Depends(rate_limit_dep),
    _user=Depends(require_user),
) -> Dict[str, Any]:
    async with Session() as s:
        ma = await s.get(MediaAsset, body.media_id)
        if not ma:
            raise HTTPException(status_code=404, detail="media not found")
        text = ma.extracted_text or ""
    from intelligence.pipeline.run import run_preview
    res = run_preview(text, test_mode=body.test_mode)
    return {"overall": res.get("overall", {}), "claims": res.get("claims", []), "methodology": res.get("methodology", {})}

@router.post("/mobile/commit_from_media")
async def commit_from_media(
    body: CommitFromMediaBody,
    _rl=Depends(rate_limit_dep),
    user=Depends(require_user),
) -> Dict[str, Any]:
    async with Session() as s:
        ma = await s.get(MediaAsset, body.media_id)
        if not ma:
            raise HTTPException(status_code=404, detail="media not found")
        text = ma.extracted_text or ""
    # Run pipeline and persist as normal analysis
    res = __import__("intelligence.pipeline.run", fromlist=["run_preview"]).run_preview(text, test_mode=body.test_mode)
    # Persist into the EXISTING analysis created at upload time to avoid extra writer contention
    analysis_id = await persist_result_into_analysis(
        analysis_id=ma.analysis_id,
        user_id=user.get("sub"),
        input_type=ma.kind,
        original_uri=ma.storage_uri,
        result=res,
    )
    return {"analysis_id": analysis_id, "overall": res.get("overall", {}), "claims_count": len(res.get("claims", []))}