from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base
import logging


from . import config


# ============================================================
# POSTGRESQL / SUPABASE
# ============================================================

def resolve_postgres_connection_url(database_url: str, *, is_vercel: bool):
    """Choose the appropriate Supavisor mode without editing DATABASE_URL.

    Local Uvicorn is a long-lived process, so use the shared Supabase session
    pooler (port 5432) when its URL was copied from the transaction pooler
    (port 6543). Vercel remains on transaction mode (6543), which is intended
    for short-lived serverless invocations. Direct DB URLs and non-Supabase
    PostgreSQL URLs are left untouched.
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

    configured_url = make_url(config.DATABASE_URL)
    engine_url = resolve_postgres_connection_url(
        config.DATABASE_URL,
        is_vercel=config.IS_VERCEL,
    )
    if engine_url.port != configured_url.port:
        logging.getLogger("prismo").info(
            "Local Supabase connection is using session pooler mode (port 5432)."
        )

    connect_args = {
        # The shared pooler on 5432 is session mode for local long-lived Uvicorn.
        # Vercel keeps transaction mode on 6543 in the URL supplied by deployment.
        "prepare_threshold": None,
        "sslmode": "require",
        "connect_timeout": 3,
        "application_name": "prismo-local",
    }

    if "sslmode=" not in str(engine_url):
        connect_args["sslmode"] = "require"

    engine = create_engine(
        engine_url,
        # Keep the existing modest connection pool to avoid opening unnecessary
        # Supabase connections. Session pooling is appropriate for local Uvicorn.
        pool_size=3,
        max_overflow=2,
        pool_timeout=3,
        pool_recycle=900,
        pool_pre_ping=False,
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