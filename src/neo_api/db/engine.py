import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

SQL_DB_URL = os.getenv("SQL_DB_URL", "sqlite+aiosqlite:///./data/app.db")

NOSQL_DB_URL = os.getenv("NOSQL_DB_URL", "mongodb://localhost:27017/nba_ml")

engine = create_async_engine(SQL_DB_URL, pool_pre_ping=True, future=True, echo=False)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    future=True,
)


class Base(DeclarativeBase):
    pass


if "sqlite" in SQL_DB_URL:

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA synchronous=NORMAL;")
        cur.close()


#mongodb_client = AsyncIOMotorClient(NOSQL_DB_URL)
#mongodb = mongodb_client.nba_ml


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection for FastAPI"""
    async with AsyncSessionLocal() as session:
        yield session
        yield session

#
#async def get_mongo():
#    """Dependency injection for MongoDB"""
#    return mongodb
#