import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", DATABASE_URL)

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env")

sync_url = DATABASE_URL
if sync_url.startswith("postgresql+asyncpg://"):
    sync_url = sync_url.replace("postgresql+asyncpg://", "postgresql://", 1)

db_ssl = os.getenv("DB_SSL", "true").lower() not in ("false", "0")
connect_args = {"ssl": "require"} if db_ssl else {}

engine = create_engine(sync_url, pool_pre_ping=True, connect_args=connect_args)
async_engine = create_async_engine(ASYNC_DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
