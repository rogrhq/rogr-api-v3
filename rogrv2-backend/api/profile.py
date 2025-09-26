from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from infrastructure.auth.deps import require_user
from infrastructure.http.limits import rate_limit_dep
from database.users import get_or_create_user_id, set_handle_for_user, get_user_by_handle, get_user_by_email
from database.repo import follow_user, unfollow_user, list_following_ids
from database.notify import create_notification

router = APIRouter()

class HandleBody(BaseModel):
    handle: str

@router.get("/profile/me")
async def profile_me(_rl=Depends(rate_limit_dep), user=Depends(require_user)) -> Dict[str, Any]:
    uid = await get_or_create_user_id(user.get("sub",""))
    return {"sub": user.get("sub",""), "user_id": uid}

@router.post("/profile/handle")
async def profile_set_handle(body: HandleBody, _rl=Depends(rate_limit_dep), user=Depends(require_user)) -> Dict[str, Any]:
    uid = await get_or_create_user_id(user.get("sub",""))
    await set_handle_for_user(uid, body.handle)
    return {"ok": True, "handle": body.handle}

class FollowBody(BaseModel):
    target: str
    kind: str = "handle"  # "handle" | "email"

@router.post("/profile/follow")
async def profile_follow(body: FollowBody, _rl=Depends(rate_limit_dep), user=Depends(require_user)) -> Dict[str, Any]:
    follower_uid = await get_or_create_user_id(user.get("sub",""))
    # resolve followee
    followee_uid: Optional[str] = None
    if body.kind == "handle":
        u = await get_user_by_handle(body.target)
        if u:
            followee_uid = u.id
        else:
            raise HTTPException(status_code=404, detail="target handle not found")
    elif body.kind == "email":
        u = await get_user_by_email(body.target)
        if not u:
            # create user row for that email
            followee_uid = await get_or_create_user_id(body.target)
        else:
            followee_uid = u.id
    else:
        raise HTTPException(status_code=400, detail="invalid kind")
    if follower_uid == followee_uid:
        raise HTTPException(status_code=400, detail="cannot follow self")
    await follow_user(follower_uid, followee_uid)
    # Notify the followee
    await create_notification(
        user_id=followee_uid,
        kind="follow",
        payload={"follower_user_id": follower_uid, "follower_sub": user.get("sub","")},
        dedupe_key=f"follow:{follower_uid}->{followee_uid}",
    )
    return {"ok": True}

@router.post("/profile/unfollow")
async def profile_unfollow(body: FollowBody, _rl=Depends(rate_limit_dep), user=Depends(require_user)) -> Dict[str, Any]:
    follower_uid = await get_or_create_user_id(user.get("sub",""))
    # resolve
    followee_uid: Optional[str] = None
    if body.kind == "handle":
        u = await get_user_by_handle(body.target)
        if not u:
            return {"ok": True}  # idempotent
        followee_uid = u.id
    elif body.kind == "email":
        u = await get_user_by_email(body.target)
        followee_uid = u.id if u else None
    else:
        raise HTTPException(status_code=400, detail="invalid kind")
    if followee_uid:
        await unfollow_user(follower_uid, followee_uid)
    return {"ok": True}

@router.get("/profile/following")
async def profile_following(_rl=Depends(rate_limit_dep), user=Depends(require_user)) -> Dict[str, Any]:
    uid = await get_or_create_user_id(user.get("sub",""))
    ids = await list_following_ids(uid)
    return {"following_ids": ids}