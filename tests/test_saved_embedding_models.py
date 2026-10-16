from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from unittest.mock import patch

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

    def test_saved_embedding_model_can_be_deleted_by_model_and_endpoint(self):
        saved = self.client.post(
            "/api/settings/saved-embedding-models",
            json={
                "model_id": "qwen/qwen3-embedding-8b",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": "embedding-delete-secret",
            },
        )
        assert saved.status_code == 200, saved.text

        deleted = self.client.delete(
            "/api/settings/saved-embedding-models",
            params={
                "model_id": "qwen/qwen3-embedding-8b",
                "base_url": "https://openrouter.ai/api/v1/",
            },
        )
        assert deleted.status_code == 200, deleted.text
        assert deleted.json()["deleted"] is True
        assert self.client.get("/api/settings/saved-embedding-models").json() == []

    def test_saved_embedding_model_can_be_activated_without_changing_chat_settings(self):
        self.client.put("/api/settings", json={"chat_model": "keep-chat", "base_url": "https://chat.example/v1", "api_key": "chat-secret", "use_default_provider": False})
        self.client.post("/api/settings/saved-embedding-models", json={
            "model_id": "qwen/qwen3-embedding-8b", "base_url": "https://openrouter.ai/api/v1", "api_key": "embedding-use-secret",
        })
        response = self.client.post("/api/settings/saved-embedding-models/use", json={
            "model_id": "qwen/qwen3-embedding-8b", "base_url": "https://openrouter.ai/api/v1",
        })
        assert response.status_code == 200, response.text
        settings = self.client.get("/api/settings").json()
        assert settings["chat_model"] == "keep-chat"
        assert settings["base_url"] == "https://chat.example/v1"
        assert settings["embedding_use_default_provider"] is False
        assert settings["separate_embedding_provider"] is True
        assert settings["embedding_model"] == "qwen/qwen3-embedding-8b"
        assert settings["embedding_base_url"] == "https://openrouter.ai/api/v1"
        assert settings["embedding_api_key_set"] is True
        assert "embedding-use-secret" not in response.text

    def test_saved_embedding_model_test_calls_embedding_endpoint_and_does_not_change_settings(self):
        self.client.post("/api/settings/saved-embedding-models", json={
            "model_id": "qwen/qwen3-embedding-8b", "base_url": "https://openrouter.ai/api/v1", "api_key": "embedding-test-secret",
        })
        with patch("app.routers.settings.llm_client.embed_text", return_value=[0.0] * 8) as embed:
            response = self.client.post("/api/settings/saved-embedding-models/test", json={
                "model_id": "qwen/qwen3-embedding-8b", "base_url": "https://openrouter.ai/api/v1",
            })
        assert response.status_code == 200, response.text
        assert response.json()["ok"] is True
        provider = embed.call_args.args[1]
        assert provider.embedding_model == "qwen/qwen3-embedding-8b"
        assert provider.embedding_base_url == "https://openrouter.ai/api/v1"
        assert provider.embedding_api_key == "embedding-test-secret"
        assert self.client.get("/api/settings").json()["embedding_use_default_provider"] is True

    def test_embedding_delete_requires_matching_endpoint(self):
        self.client.post(
            "/api/settings/saved-embedding-models",
            json={
                "model_id": "example/embed",
                "base_url": "https://provider.example/v1",
                "api_key": "embedding-secret",
            },
        )
        response = self.client.delete(
            "/api/settings/saved-embedding-models",
            params={"model_id": "example/embed", "base_url": "https://other.example/v1"},
        )
        assert response.status_code == 404
        assert len(self.client.get("/api/settings/saved-embedding-models").json()) == 1

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


def test_saved_model_ui_has_one_click_delete_and_collapsed_chat_registry():
    root = Path(__file__).resolve().parents[1]
    dashboard = (root / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    html = (root / "frontend" / "dashboard.html").read_text(encoding="utf-8")
    assert 'className = "saved-model-delete-btn"' in dashboard
    assert 'method: "DELETE"' in dashboard
    assert 'id="savedChatModelsDetails"' in html
    assert '<details class="saved-chat-models-panel" id="savedChatModelsDetails"' in html
    assert 'class="saved-model-pills" id="savedEmbeddingModelsList" role="list"' in html
    assert 'ai-inline-help' in html
