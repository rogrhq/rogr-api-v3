import asyncio, sys, pathlib
# Ensure imports work no matter where the test is invoked from
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from database.session import engine
from database.models import Base

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("PASS")

if __name__ == "__main__":
    asyncio.run(main())