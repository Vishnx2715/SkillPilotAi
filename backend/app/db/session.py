from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

engine = None
AsyncSessionLocal = None

if settings.DATABASE_URL:
    _url = settings.DATABASE_URL

    # Guard: production must not use SQLite
    if settings.ENVIRONMENT == "production" and _url.startswith("sqlite"):
        raise RuntimeError(
            "DATABASE_URL must be a PostgreSQL URL in production, not SQLite."
        )

    # Guard: asyncpg must be importable when using postgres dialect
    if _url.startswith("postgresql+asyncpg"):
        try:
            import asyncpg  # noqa: F401
        except ImportError:
            raise RuntimeError(
                "asyncpg is not installed. Add asyncpg to requirements.txt "
                "and ensure PYTHON_VERSION=3.11.9 is set on Render."
            )

    _connect_args = {"check_same_thread": False} if "sqlite" in _url else {}

    engine = create_async_engine(
        _url,
        echo=False,
        future=True,
        connect_args=_connect_args,
    )
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def get_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    if AsyncSessionLocal is None:
        yield None
        return
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
