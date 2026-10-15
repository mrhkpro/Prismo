from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app import models
from app.main import app
from app.security import get_current_user


class TestSavedEmbeddingModelRegistry:
    def setup_method(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        db = self.Session()
        user = models.User(
            username="saved-embedding-owner",
            password_hash="test-hash",
            role=models.UserRole.user,
            is_active=True,
        )
        db.add(user)
        db.flush()
        db.add(models.UserSettings(user_id=user.id))
        db.commit()
        db.refresh(user)
        db.close()
        self.user = user

        def override_db():
            session = self.Session()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = lambda: self.user
        self.client = TestClient(app)

    def teardown_method(self):
        app.dependency_overrides.clear()
        self.engine.dispose()

    def test_explicit_embedding_profile_is_saved_and_key_never_returned(self):
        secret = "embedding-secret-never-return"
        response = self.client.post(
            "/api/settings/saved-embedding-models",
            json={
                "model_id": "qwen/qwen3-embedding-8b",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": secret,
            },
        )
        assert response.status_code == 200, response.text
        assert response.json() == {
            "model_id": "qwen/qwen3-embedding-8b",
            "base_url": "https://openrouter.ai/api/v1",
        }
        assert secret not in response.text

        listing = self.client.get("/api/settings/saved-embedding-models")
        assert listing.status_code == 200, listing.text
        assert listing.json() == [{
            "model_id": "qwen/qwen3-embedding-8b",
            "base_url": "https://openrouter.ai/api/v1",
        }]
        assert secret not in listing.text

    def test_missing_embedding_table_returns_migration_instructions(self):
        models.SavedEmbeddingModel.__table__.drop(self.engine)
        response = self.client.get("/api/settings/saved-embedding-models")
        assert response.status_code == 503
        assert "013_repair_saved_model_registries.sql" in response.json()["detail"]


def test_saved_model_lists_are_only_shown_for_custom_provider_modes():
    dashboard = (Path(__file__).resolve().parents[1] / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    assert 'savedChatPanel.style.display = useDefault ? "none" : "block"' in dashboard
    assert 'savedEmbeddingPanel.style.display = useDefault ? "none" : "block"' in dashboard
    assert 'apiCall("/api/settings/saved-embedding-models", {' in dashboard
    assert 'apiCall("/api/settings/saved-embedding-models/current"' not in dashboard
