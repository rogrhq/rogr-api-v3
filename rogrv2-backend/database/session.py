from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool, StaticPool
import os, asyncio
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
import sqlite3

DATABASE_URL = os.environ["DATABASE_URL"]

if DATABASE_URL.startswith("sqlite+aiosqlite"):
    # HARDENED SQLITE CONFIG FOR TESTS:
    # - StaticPool: reuse a single physical connection (prevents multi-connection lock storms)
    # - Exclusive locking, no WAL, long busy_timeout
    # - Ensure URI mode honored (cache=shared helps readers)
    connect_args = {"timeout": 30}
    engine = create_async_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        poolclass=StaticPool,  # single connection reused
        connect_args=connect_args,
    )
    @event.listens_for(engine.sync_engine, "connect")
    def _sqlite_pragmas(dbapi_connection, connection_record):
        cur = dbapi_connection.cursor()
        try:
            cur.execute("PRAGMA journal_mode=DELETE;")   # simple journaling avoids WAL writer blocks
            cur.execute("PRAGMA synchronous=NORMAL;")
            cur.execute("PRAGMA locking_mode=EXCLUSIVE;")# keep exclusive lock to avoid thrash
            cur.execute("PRAGMA busy_timeout=30000;")
            cur.execute("PRAGMA temp_store=MEMORY;")
            cur.execute("PRAGMA cache_size=10000;")
        finally:
            cur.close()
else:
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

Session = async_sessionmaker(engine, expire_on_commit=False)

_IS_SQLITE = DATABASE_URL.startswith("sqlite+aiosqlite")
# A single-process async lock to serialize WRITE transactions on SQLite.
_WRITE_LOCK: asyncio.Lock = asyncio.Lock()

def is_sqlite() -> bool:
    return _IS_SQLITE

def write_lock() -> asyncio.Lock:
    """Use as:  async with write_lock(): ...   (no-op semantics for non-SQLite callers)"""
    return _WRITE_LOCK

async def commit_with_retry(session, *, retries: int = 6, base_delay: float = 0.05):
    """
    For SQLite only: retry commits when hitting 'database is locked'.
    Exponential backoff capped to ~1.6s total by default.
    """
    if not _IS_SQLITE:
        await session.commit()
        return
    attempt = 0
    delay = base_delay
    while True:
        try:
            await session.commit()
            return
        except OperationalError as e:
            msg = str(e).lower()
            if "database is locked" in msg or "database is busy" in msg:
                attempt += 1
                if attempt > retries:
                    raise
                await asyncio.sleep(delay)
                delay = min(delay * 2, 0.5)
                continue
            raise
        except sqlite3.OperationalError as e:
            msg = str(e).lower()
            if "database is locked" in msg or "database is busy" in msg:
                attempt += 1
                if attempt > retries:
                    raise
                await asyncio.sleep(delay)
                delay = min(delay * 2, 0.5)
                continue
            raise