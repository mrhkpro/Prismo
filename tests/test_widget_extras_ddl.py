"""رگرسیون: ساخت ستون widget_extras نباید اتصال دوم باز کند (روی PostgreSQL باعث deadlock می‌شد)."""
from unittest.mock import patch

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.services import widget_extras


def _db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def test_ensure_column_runs_on_the_request_connection_only():
    engine, db = _db()
    try:
        assert not widget_extras._column_exists(db)
        # مسیر قدیمیِ باگ: engine.begin() = اتصال مستقل از نشست درخواست
        with patch.object(engine, "begin", side_effect=AssertionError("second connection opened")):
            assert widget_extras._ensure_column(db) is True
        assert widget_extras._column_exists(db)
        db.execute(text("SELECT widget_extras FROM user_settings"))
    finally:
        db.close()
        engine.dispose()


def test_ensure_column_is_a_noop_when_column_already_exists():
    engine, db = _db()
    try:
        db.execute(text("ALTER TABLE user_settings ADD COLUMN widget_extras TEXT"))
        db.commit()
        executed = []
        orig = db.execute
        db.execute = lambda stmt, *a, **k: (executed.append(str(stmt)), orig(stmt, *a, **k))[1]
        assert widget_extras._ensure_column(db) is True
        assert not any("ALTER" in s.upper() for s in executed)
    finally:
        db.close()
        engine.dispose()
