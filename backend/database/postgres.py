from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()


async def create_tables():
    """Create all tables in the database"""
    from database.schemas import Base as SchemaBase
    async with engine.begin() as conn:
        await conn.run_sync(SchemaBase.metadata.create_all)


@asynccontextmanager
async def get_db():
    """Dependency for getting async database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session():
    """FastAPI dependency"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
