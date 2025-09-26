#!/usr/bin/env python3
"""
Idempotent migration entrypoint.

Modes:
- Default: create_all from ORM metadata (safe for SQLite/dev)
- If USE_ALEMBIC=1 and alembic/versions non-empty: programmatic alembic upgrade head
Exit code 0 on success.
"""
import os, sys, asyncio, pathlib

# Ensure a DATABASE_URL exists even when not provided by the orchestrator.
# Use a local SQLite file by default to keep tests hermetic.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///rogr_dev.sqlite3")

USE_ALEMBIC = os.getenv("USE_ALEMBIC","0") == "1"

async def create_all():
    from database.session import engine
    from database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def _has_versions() -> bool:
    p = pathlib.Path("alembic/versions")
    return p.exists() and any(p.iterdir())

def _alembic_upgrade_head():
    from alembic.config import Config
    from alembic import command
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")

def main():
    if USE_ALEMBIC and _has_versions():
        try:
            _alembic_upgrade_head()
            print("migrate_cli: alembic upgrade head OK")
            return 0
        except Exception as e:
            print(f"migrate_cli: alembic failed: {e}", file=sys.stderr)
            return 2
    # Fallback to create_all
    try:
        asyncio.run(create_all())
        print("migrate_cli: metadata.create_all OK")
        return 0
    except Exception as e:
        print(f"migrate_cli: create_all failed: {e}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())