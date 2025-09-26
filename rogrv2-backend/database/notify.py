from __future__ import annotations
import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import Session, commit_with_retry, is_sqlite, write_lock
from database.models import Notification
from database.repo import ensure_schema
from database.users import get_or_create_user_id

async def create_notification(
    *,
    user_id: str,
    kind: str,
    payload: Dict[str, Any],
    dedupe_key: Optional[str] = None,
) -> str:
    """
    Create a notification if not already present via dedupe_key. Returns notification id.
    """
    await ensure_schema()
    # Accept either internal UUID or external subject (email). If it's an email, map to UUID.
    if "@" in (user_id or ""):
        user_id = await get_or_create_user_id(user_id)
    guard = write_lock() if is_sqlite() else None
    if guard:
        async with guard:
            async with Session() as s:  # type: AsyncSession
                if dedupe_key:
                    existing = (await s.execute(select(Notification).where(Notification.dedupe_key == dedupe_key))).scalars().first()
                    if existing:
                        return existing.id
                n = Notification(user_id=user_id, kind=kind, payload_json=payload, dedupe_key=dedupe_key)
                s.add(n)
                await commit_with_retry(s)
                return n.id
    async with Session() as s:  # non-SQLite path
        if dedupe_key:
            existing = (await s.execute(select(Notification).where(Notification.dedupe_key == dedupe_key))).scalars().first()
            if existing:
                return existing.id
        n = Notification(user_id=user_id, kind=kind, payload_json=payload, dedupe_key=dedupe_key)
        s.add(n)
        await commit_with_retry(s)
        return n.id

async def list_notifications(user_id: str, *, unread_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
    await ensure_schema()
    # Map external subject (email) to internal UUID if needed
    if "@" in (user_id or ""):
        user_id = await get_or_create_user_id(user_id)
    async with Session() as s:
        q = select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc()).limit(limit)
        rows = (await s.execute(q)).scalars().all()
        out: List[Dict[str, Any]] = []
        for n in rows:
            if unread_only and n.read_at is not None:
                continue
            out.append({
                "id": n.id,
                "kind": n.kind,
                "payload": n.payload_json,
                "created_at": n.created_at.replace(microsecond=0).isoformat() + "Z",
                "read": n.read_at is not None,
            })
        return out

async def ack_notifications(user_id: str, ids: List[str]) -> int:
    """
    Mark notifications as read for user_id. Returns count updated.
    """
    await ensure_schema()
    if not ids:
        return 0
    # Map external subject (email) to internal UUID if needed
    if "@" in (user_id or ""):
        user_id = await get_or_create_user_id(user_id)
    guard = write_lock() if is_sqlite() else None
    if guard:
        async with guard:
            async with Session() as s:
                now = datetime.datetime.utcnow()
                res = await s.execute(
                    update(Notification)
                    .where((Notification.user_id == user_id) & (Notification.id.in_(ids)))
                    .values(read_at=now)
                )
                await commit_with_retry(s)
                return res.rowcount or 0
    async with Session() as s:
        now = datetime.datetime.utcnow()
        res = await s.execute(
            update(Notification)
            .where((Notification.user_id == user_id) & (Notification.id.in_(ids)))
            .values(read_at=now)
        )
        await commit_with_retry(s)
        return res.rowcount or 0