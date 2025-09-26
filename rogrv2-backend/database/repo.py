from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import engine, Session
from database.models import Base, Analysis, Claim, FeedPost, Follow
from database.users import get_or_create_user_id

_schema_ready = False

async def ensure_schema() -> None:
    global _schema_ready
    if _schema_ready:
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    _schema_ready = True

async def save_analysis_with_claims(
    *,
    user_id: Optional[str],
    input_type: str,
    original_uri: Optional[str],
    result: Dict[str, Any],
) -> str:
    """
    Persist minimal fields for Analysis + primary claims for search, and a FeedPost.
    """
    await ensure_schema()
    async with Session() as s:  # type: AsyncSession
        a = Analysis(
            user_id=None,  # set below after we ensure a real user row
            input_type=input_type,
            original_uri=original_uri,
            status="completed",
            total_grade_numeric=int(result.get("overall", {}).get("score", 0)),
            total_label=str(result.get("overall", {}).get("label", "")),
            summary_capsule_json=None,
            ifcn_methodology_json=result.get("methodology", {}),
        )
        s.add(a)
        await s.flush()  # populate a.id

        # Store all claims returned (text + tier + priority)
        claims: List[Claim] = []
        for c in result.get("claims", []):
            claims.append(
                Claim(
                    analysis_id=a.id,
                    text=(c.get("text") or "")[:2000],
                    tier=c.get("tier", "primary"),
                    priority=int(c.get("priority", 0)),
                    entities_json=None,
                    scope_json=None,
                )
            )
        if claims:
            s.add_all(claims)

        # ensure a real user id (row) exists and attach to analysis/feed post
        resolved_uid: Optional[str] = None
        if user_id:
            resolved_uid = await get_or_create_user_id(user_id)
        a.user_id = resolved_uid
        s.add(FeedPost(analysis_id=a.id, author_id=resolved_uid or "", visibility="public"))

        await s.commit()
        return a.id

async def follow_user(follower_id: str, followee_id: str) -> None:
    await ensure_schema()
    async with Session() as s:
        # upsert-like: delete if exists then insert to avoid dup primary key issues
        await s.merge(Follow(follower_id=follower_id, followee_id=followee_id))
        await s.commit()

async def unfollow_user(follower_id: str, followee_id: str) -> None:
    await ensure_schema()
    async with Session() as s:
        await s.execute(
            Follow.__table__.delete().where(
                (Follow.follower_id == follower_id) & (Follow.followee_id == followee_id)
            )
        )
        await s.commit()

async def list_following_ids(follower_id: str) -> list[str]:
    await ensure_schema()
    async with Session() as s:
        rows = (await s.execute(select(Follow.followee_id).where(Follow.follower_id == follower_id))).all()
        return [r[0] for r in rows]

async def load_feed_page(cursor_iso: Optional[str], limit: int) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Return latest feed items; cursor is an ISO timestamp string (created_at).
    DB-agnostic (works on SQLite tests and Postgres prod).
    """
    await ensure_schema()
    async with Session() as s:
        q = select(FeedPost, Analysis).join(Analysis, FeedPost.analysis_id == Analysis.id)
        if cursor_iso:
            _c = cursor_iso.strip()
            try:
                if _c.endswith("Z"):
                    cursor_dt = datetime.fromisoformat(_c.replace("Z", "+00:00"))
                else:
                    cursor_dt = datetime.fromisoformat(_c)
                if cursor_dt.tzinfo is None:
                    cursor_dt = cursor_dt.replace(tzinfo=timezone.utc)
                else:
                    cursor_dt = cursor_dt.astimezone(timezone.utc)
                q = q.where(Analysis.created_at < cursor_dt)
            except Exception:
                # Ignore bad cursor and just fetch latest
                pass
        q = q.order_by(desc(Analysis.created_at)).limit(limit)
        rows = (await s.execute(q)).all()

        items: List[Dict[str, Any]] = []
        next_cursor: Optional[str] = None
        for fp, an in rows:
            items.append({
                "id": getattr(fp, "id", f"post-{an.id}"),
                "analysis_id": an.id,
                "author_handle": "",
                "visibility": "public",
                "created_at": an.created_at.replace(microsecond=0).isoformat() + "Z",
                "headline": "",
                "overall": {"score": an.total_grade_numeric or 0, "label": an.total_label or ""},
            })
        if rows:
            # Use full precision (with microseconds) for cursor to avoid skipping items
            last_an = rows[-1][1]
            _dt = last_an.created_at.astimezone(timezone.utc)
            next_cursor = _dt.isoformat().replace("+00:00", "Z")
        return items, next_cursor

async def load_feed_page_for_user(user_id: Optional[str], following_only: bool, cursor_iso: Optional[str], limit: int) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    If following_only is True and user_id is present, return posts authored by followees.
    Otherwise, return global feed (same as load_feed_page).
    """
    if not following_only or not user_id:
        return await load_feed_page(cursor_iso, limit)
    await ensure_schema()
    async with Session() as s:
        followees = await list_following_ids(user_id)
        if not followees:
            return [], None
        q = select(FeedPost, Analysis).join(Analysis, FeedPost.analysis_id == Analysis.id)
        q = q.where(FeedPost.author_id.in_(followees))
        q = q.order_by(desc(Analysis.created_at)).limit(limit)
        rows = (await s.execute(q)).all()
        items = []
        next_cursor = None
        for fp, an in rows:
            items.append({
                "id": fp.id if hasattr(fp, "id") else f"post-{an.id}",
                "analysis_id": an.id,
                "author_handle": "",
                "visibility": "public",
                "created_at": an.created_at.replace(microsecond=0).isoformat() + "Z",
                "headline": "",
                "overall": {"score": an.total_grade_numeric or 0, "label": an.total_label or ""},
            })
        if rows:
            last_an = rows[-1][1]
            next_cursor = last_an.created_at.replace(microsecond=0).isoformat() + "Z"
        return items, next_cursor

async def search_archive(q: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Very simple LIKE against Claim.text; return distinct analyses with their first claim.
    """
    await ensure_schema()
    q = (q or "").strip()
    async with Session() as s:
        if not q:
            aq = select(Analysis).order_by(desc(Analysis.created_at)).limit(limit)
            analyses = (await s.execute(aq)).scalars().all()
        else:
            cq = select(Claim.analysis_id).where(Claim.text.ilike(f"%{q}%")).limit(200)
            a_ids = [r[0] for r in (await s.execute(cq)).all()]
            if not a_ids:
                return []
            aq = select(Analysis).where(Analysis.id.in_(a_ids)).limit(limit)
            analyses = (await s.execute(aq)).scalars().all()

        out: List[Dict[str, Any]] = []
        for an in analyses:
            c1 = (await s.execute(
                select(Claim).where(Claim.analysis_id == an.id).order_by(Claim.priority, Claim.id).limit(1)
            )).scalars().first()
            out.append({
                "analysis_id": an.id,
                "created_at": an.created_at.replace(microsecond=0).isoformat() + "Z",
                "claims": ([] if not c1 else [{"text": c1.text, "tier": c1.tier, "score_numeric": an.total_grade_numeric or 0, "label": an.total_label or ""}]),
                "overall": {"score": an.total_grade_numeric or 0, "label": an.total_label or ""},
            })
        return out