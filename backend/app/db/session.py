import logging
import re
from typing import AsyncGenerator, Optional

from sqlalchemy import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

logger = logging.getLogger("skillpilot.db")

engine = None
AsyncSessionLocal = None

# ── Render internal DB host pattern ──────────────────────────────────────────
_RENDER_INTERNAL_RE = re.compile(r"^dpg-[a-z0-9]+-a$")

# ── Placeholder hosts that should never reach production ─────────────────────
_PLACEHOLDER_HOSTS = {"", "host", "hostname", "localhost", "127.0.0.1", "HOST"}


def _validate_and_build_engine():
    global engine, AsyncSessionLocal

    raw_url = settings.DATABASE_URL

    # ── T3: empty URL ─────────────────────────────────────────────────────────
    if not raw_url:
        raise RuntimeError(
            "DATABASE_URL is empty. "
            "Set it in the Render dashboard → Environment → DATABASE_URL."
        )

    # SQLite branch — no network, no SSL, no asyncpg needed
    if "sqlite" in raw_url:
        if settings.ENVIRONMENT == "production":
            raise RuntimeError(
                "DATABASE_URL must be a PostgreSQL URL in production, not SQLite."
            )
        engine = create_async_engine(
            raw_url, echo=False, future=True,
            connect_args={"check_same_thread": False},
        )
        AsyncSessionLocal = async_sessionmaker(
            bind=engine, class_=AsyncSession,
            expire_on_commit=False, autocommit=False, autoflush=False,
        )
        logger.info("DB target: driver=sqlite (local dev)")
        return

    # ── asyncpg guard ─────────────────────────────────────────────────────────
    try:
        import asyncpg  # noqa: F401
    except ImportError:
        raise RuntimeError(
            "asyncpg is not installed. "
            "Ensure asyncpg>=0.31.0 is in requirements.txt and "
            "PYTHON_VERSION=3.11.9 is set on Render."
        )

    # ── Parse URL safely ──────────────────────────────────────────────────────
    try:
        u = make_url(raw_url)
    except Exception as exc:
        raise RuntimeError(f"Cannot parse DATABASE_URL: {exc}") from exc

    host = u.host or ""
    port = u.port
    db   = u.database or ""
    drv  = u.drivername

    # Safe diagnostic log — NO username or password ever logged
    logger.info(
        "DB target: driver=%s host=%s port=%s db=%s",
        drv, host, port, db,
    )

    # ── H3: placeholder / localhost ───────────────────────────────────────────
    if host in _PLACEHOLDER_HOSTS and settings.ENVIRONMENT == "production":
        raise RuntimeError(
            f"DATABASE_URL host looks like a placeholder/localhost: '{host}'. "
            "Replace with your real Supabase or Render Postgres host."
        )

    # ── H1: Supabase direct host (IPv6-only, fails on Render) ─────────────────
    if host.startswith("db.") and host.endswith(".supabase.co"):
        raise RuntimeError(
            f"Supabase direct host '{host}' is IPv6-only and will fail on Render. "
            "Use the Session pooler URL instead: "
            "Supabase → Project → Settings → Database → "
            "Connection string → Session mode (port 5432), "
            "host = aws-0-<region>.pooler.supabase.com"
        )

    # ── H2: Render internal host warning ──────────────────────────────────────
    if _RENDER_INTERNAL_RE.match(host):
        logger.warning(
            "Render internal DB host detected (%s). "
            "Make sure this Postgres service is in the SAME region and "
            "workspace as the web service, or DNS will fail.",
            host,
        )

    # ── T6: Supabase transaction pooler (port 6543) — no statement cache ──────
    connect_args: dict = {}
    if port == 6543:
        logger.warning(
            "Supabase transaction pooler (port 6543) detected. "
            "Setting statement_cache_size=0. "
            "Consider switching to Session pooler (port 5432) for full SQLAlchemy support."
        )
        connect_args["statement_cache_size"] = 0

    # ── T5: require SSL for non-Render-internal hosts ─────────────────────────
    is_render_internal = bool(_RENDER_INTERNAL_RE.match(host))
    url_str = str(u)
    has_ssl_param = "ssl=" in url_str or "sslmode=" in url_str
    if not is_render_internal and not has_ssl_param:
        connect_args["ssl"] = "require"
        logger.info("SSL=require added for non-internal host.")

    engine = create_async_engine(
        raw_url,
        echo=False,
        future=True,
        connect_args=connect_args,
    )
    AsyncSessionLocal = async_sessionmaker(
        bind=engine, class_=AsyncSession,
        expire_on_commit=False, autocommit=False, autoflush=False,
    )


# Run at import time — loud failure if URL is obviously wrong
_validate_and_build_engine()


async def get_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    if AsyncSessionLocal is None:
        yield None
        return
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
