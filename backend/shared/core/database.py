from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
from .config import settings

# Read-write database engine (für Admin API)
engine_rw = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Read-only database engine (für Client API)
# Falls keine separate Read-only URL konfiguriert ist, verwende die normale URL
readonly_url = settings.database_url_readonly or settings.database_url
engine_ro = create_async_engine(
    readonly_url,
    echo=settings.database_echo,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Session factories
async_session_maker_rw = async_sessionmaker(
    engine_rw,
    class_=AsyncSession,
    expire_on_commit=False,
)

async_session_maker_ro = async_sessionmaker(
    engine_ro,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Backward compatibility - verwende Read-write als Standard
engine = engine_rw
async_session_maker = async_session_maker_rw

# Declarative base for ORM models
class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )

# Dependencies für verschiedene Session-Typen
async def get_async_session_rw() -> AsyncSession:
    """Read-write database session dependency für Admin API"""
    async with async_session_maker_rw() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_async_session_ro() -> AsyncSession:
    """Read-only database session dependency für Client API"""
    async with async_session_maker_ro() as session:
        try:
            yield session
        finally:
            await session.close()

# Backward compatibility
async def get_async_session() -> AsyncSession:
    """Default database session dependency - verwendet Read-write"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

# Database lifecycle management
async def create_db_and_tables():
    """Create database tables"""
    async with engine_rw.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """Close database connections"""
    await engine_rw.dispose()
    await engine_ro.dispose() 