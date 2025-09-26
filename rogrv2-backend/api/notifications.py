from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Any, Dict, List
from infrastructure.auth.deps import require_user
from infrastructure.http.limits import rate_limit_dep
from database.notify import list_notifications, ack_notifications

router = APIRouter()

@router.get("/notifications")
async def notifications_list(
    _rl=Depends(rate_limit_dep),
    user=Depends(require_user),
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
) -> Dict[str, Any]:
    items = await list_notifications(user.get("sub",""), unread_only=unread_only, limit=limit)
    return {"items": items}

class AckBody(BaseModel):
    ids: List[str]

@router.post("/notifications/ack")
async def notifications_ack(
    body: AckBody,
    _rl=Depends(rate_limit_dep),
    user=Depends(require_user),
) -> Dict[str, Any]:
    count = await ack_notifications(user.get("sub",""), body.ids or [])
    return {"updated": count}