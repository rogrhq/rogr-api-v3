from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import os
DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
Session = async_sessionmaker(engine, expire_on_commit=False)