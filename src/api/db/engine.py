import os
from typing import AsyncGenerator

from dotenv import load_dotenv

# from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
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
    """Declarative base class for SQLAlchemy ORM models.

    This class provides the central declarative base used throughout the application
    for defining ORM models. It inherits from sqlalchemy.orm.DeclarativeBase and
    supplies a shared metadata registry and common conventions for model classes.

    Usage:
        Subclass Base to define tables and mapped classes:

            class User(Base):
                __tablename__ = "users"
                id = Column(Integer, primary_key=True)
                name = Column(String, nullable=False)

    Notes:
        - Use Base.metadata to access the MetaData object (for operations such as
          Base.metadata.create_all(engine) or Base.metadata.drop_all(engine)).
        - Keep model logic minimal; database interactions should be performed via
          sessions in repository/service layers.
        - Common fields or behaviors (e.g. timestamps, soft-delete flags, custom
          __repr__) can be implemented as mixin classes and combined with Base.

    Example:
        # Create all tables
        Base.metadata.create_all(engine)

        # Querying
        with Session(engine) as session:
            user = session.query(User).filter_by(id=1).one()

    Extensibility:
        You can extend Base with project-wide conventions, event listeners, or mixins
        to enforce consistent behavior across all models.
    """

    pass


if "sqlite" in SQL_DB_URL:

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON;")
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA synchronous=NORMAL;")
        cur.close()


# mongodb_client = AsyncIOMotorClient(NOSQL_DB_URL)
# mongodb = mongodb_client.nba_ml


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection for FastAPI"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


#
# async def get_mongo():
#    """Dependency injection for MongoDB"""
#    return mongodb
#
#
