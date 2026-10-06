from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


from . import config


# ============================================================
# POSTGRESQL / SUPABASE
# ============================================================

if config.IS_POSTGRES:

    connect_args = {
        "prepare_threshold": None,
        "sslmode": "require",
    }

    if "sslmode=" not in config.DATABASE_URL:
        connect_args["sslmode"] = "require"


    engine = create_engine(
        config.DATABASE_URL,
        pool_size=3,
        max_overflow=2,
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