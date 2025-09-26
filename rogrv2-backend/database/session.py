from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import os
from sqlalchemy import event

DATABASE_URL = os.environ["DATABASE_URL"]

if DATABASE_URL.startswith("sqlite+aiosqlite"):
    # For SQLite, avoid pooling (NullPool) and increase busy timeout; enable WAL to reduce write locks.
    engine = create_async_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        poolclass=NullPool,
        connect_args={"timeout": 30},  # seconds
    )
    @event.listens_for(engine.sync_engine, "connect")  # pragma tuning per-connection
    def _sqlite_pragmas(dbapi_connection, connection_record):
        cur = dbapi_connection.cursor()
        try:
            cur.execute("PRAGMA journal_mode=WAL;")
            cur.execute("PRAGMA synchronous=NORMAL;")
            cur.execute("PRAGMA busy_timeout=30000;")  # 30s
        finally:
            cur.close()
else:
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

Session = async_sessionmaker(engine, expire_on_commit=False)