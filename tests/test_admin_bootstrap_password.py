from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import config, models, security
from app.database import Base
from app.seed import seed_admin


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)()


def test_existing_configured_admin_password_is_synchronized(monkeypatch):
    monkeypatch.setattr(config, "ADMIN_USERNAME", "admin")
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "qwe-test-password-123")
    monkeypatch.setattr(config, "ADMIN_ORG_NAME", "Test Admin")
    engine, db = _session()
    try:
        old = models.User(
            username="admin",
            org_name="Old Admin",
            password_hash=security.hash_password("previous-password"),
            role=models.UserRole.admin,
            is_active=True,
        )
        db.add(old)
        db.commit()

        seed_admin(db)
        db.expire_all()
        saved = db.query(models.User).filter_by(username="admin").one()

        assert security.verify_password("qwe-test-password-123", saved.password_hash)
        assert not security.verify_password("previous-password", saved.password_hash)
        assert saved.role == models.UserRole.admin
        assert saved.is_active is True
        assert saved.settings is not None
    finally:
        db.close()
        engine.dispose()


def test_fresh_local_bootstrap_uses_configured_password(monkeypatch):
    monkeypatch.setattr(config, "ADMIN_USERNAME", "admin")
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "qwe-test-password-123")
    monkeypatch.setattr(config, "ADMIN_ORG_NAME", "Test Admin")
    engine, db = _session()
    try:
        seed_admin(db)
        saved = db.query(models.User).filter_by(username="admin").one()
        assert security.verify_password("qwe-test-password-123", saved.password_hash)
        assert saved.role == models.UserRole.admin
        assert saved.settings is not None
    finally:
        db.close()
        engine.dispose()


def test_supabase_bootstrap_is_opt_in_and_only_for_development(monkeypatch):
    source = (config.BASE_DIR / "app" / "main.py").read_text(encoding="utf-8")
    lifespan = source.split("async def lifespan", 1)[1].split("# ============================================================\n# APPLICATION", 1)[0]
    assert 'elif config.APP_ENV == "development" and config.BOOTSTRAP_ADMIN_ON_STARTUP' in lifespan
    assert 'os.getenv(\n    "PRISMO_BOOTSTRAP_ADMIN_ON_STARTUP", "0"' in (config.BASE_DIR / "app" / "config.py").read_text(encoding="utf-8")
