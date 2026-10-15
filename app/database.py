from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base
import logging


from . import config


# ============================================================
# POSTGRESQL / SUPABASE
# ============================================================

def resolve_postgres_connection_url(database_url: str, *, is_vercel: bool):
    """Use v2.8.1 engine behavior with the reachable local Supabase pooler.

    A local, long-running Uvicorn process uses Supabase Session Pooler (5432)
    when its configured URL points at the transaction pooler (6543). Vercel
    keeps the configured transaction-pooler URL unchanged. Direct database URLs
    and non-Supabase PostgreSQL URLs are never rewritten.
    """
    url = make_url(database_url)
    if (
        not is_vercel
        and url.host
        and url.host.lower().endswith(".pooler.supabase.com")
        and url.port == 6543
    ):
        return url.set(port=5432)
    return url

if config.IS_POSTGRES:

    connect_args = {
        # Supabase transaction-pooler (6543) should not receive a large local pool.
        # A small warm pool reduces connection churn without creating CPU spikes.
        "prepare_threshold": None,
        "sslmode": "require",
        "connect_timeout": 10,
        "application_name": "prismo-local",
    }

    if "sslmode=" not in config.DATABASE_URL:
        connect_args["sslmode"] = "require"


    engine_url = resolve_postgres_connection_url(
        config.DATABASE_URL, is_vercel=config.IS_VERCEL
    )
    if make_url(engine_url).port != make_url(config.DATABASE_URL).port:
        logging.getLogger("prismo").info(
            "Local Supabase is using session pooler port 5432."
        )

    engine = create_engine(
        engine_url,
        # Keep a few warm connections. Large pools are counterproductive for a
        # local app talking to Supabase and can trigger unnecessary CPU/network work.
        pool_size=3,
        max_overflow=2,
        pool_timeout=10,
        pool_recycle=300,
        pool_pre_ping=True,
        pool_use_lifo=True,
        connect_args=connect_args,
    )


# ============================================================
# LOCAL SQLITE
# ============================================================

else:

    engine = create_engine(
        config.DATABASE_URL,
        connect_args={
            "check_same_thread": False,
        },
    )


# ============================================================
# SESSION
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)


Base = declarative_base()


# ============================================================
# FASTAPI DATABASE DEPENDENCY
# ============================================================

def get_db():
    """
    FastAPI dependency که یک نشست دیتابیس می‌سازد
    و پس از پایان درخواست آن را می‌بندد.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()