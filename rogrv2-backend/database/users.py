from __future__ import annotations
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid, datetime

from database.session import Session
from database.models import User

def _uuid() -> str:
    return str(uuid.uuid4())

async def get_or_create_user_id(email: str) -> str:
    email = (email or "").lower().strip()
    async with Session() as s:  # type: AsyncSession
        u = (await s.execute(select(User).where(User.email == email))).scalars().first()
        if u:
            return u.id
        u = User(id=_uuid(), email=email, handle=None, created_at=datetime.datetime.utcnow(), auth_provider="jwt")
        s.add(u)
        await s.commit()
        return u.id

async def set_handle_for_user(user_id: str, handle: str) -> None:
    handle = handle.strip()
    async with Session() as s:
        u = await s.get(User, user_id)
        if not u:
            return
        u.handle = handle
        await s.commit()

async def get_user_by_handle(handle: str) -> Optional[User]:
    handle = handle.strip()
    async with Session() as s:
        return (await s.execute(select(User).where(User.handle == handle))).scalars().first()

async def get_user_by_email(email: str) -> Optional[User]:
    email = (email or "").lower().strip()
    async with Session() as s:
        return (await s.execute(select(User).where(User.email == email))).scalars().first()