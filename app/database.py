from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


from . import config


# ============================================================
# POSTGRESQL / SUPABASE
# ============================================================

if config.IS_POSTGRES:

    connect_args = {
        # Supabase transaction-pooler (6543) should not receive a large local pool.
        # A small warm pool reduces connection churn without creating CPU spikes.
        "prepare_threshold": None,
        "sslmode": "require",
        "connect_timeout": 3,
        "application_name": "prismo-local",
    }

    if "sslmode=" not in config.DATABASE_URL:
        connect_args["sslmode"] = "require"


    engine = create_engine(
        config.DATABASE_URL,
        # Keep a few warm connections. Large pools are counterproductive for a
        # local app talking to Supabase and can trigger unnecessary CPU/network work.
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