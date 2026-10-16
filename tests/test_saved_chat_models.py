from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.database import Base, get_db
from app import models
from app.main import app
from app.security import get_current_user


class TestSavedChatModelRegistry:
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
            username="saved-model-owner",
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

    def test_chat_model_profile_is_saved_upserted_and_api_key_is_not_returned(self):
        secret = "test-api-key-must-never-return"
        first = self.client.post(
            "/api/settings/saved-chat-models",
            json={
                "model_id": "cohere/command-r",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": secret,
            },
        )
        assert first.status_code == 200, first.text
        assert first.json() == {
            "model_id": "cohere/command-r",
            "base_url": "https://openrouter.ai/api/v1",
        }
        assert secret not in first.text

        second = self.client.post(
            "/api/settings/saved-chat-models",
            json={
                "model_id": "cohere/command-r",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": "updated-key",
            },
        )
        assert second.status_code == 200, second.text

        listing = self.client.get("/api/settings/saved-chat-models")
        assert listing.status_code == 200, listing.text
        assert listing.json() == [
            {"model_id": "cohere/command-r", "base_url": "https://openrouter.ai/api/v1"}
        ]
        assert "updated-key" not in listing.text

    def test_saved_chat_model_can_be_deleted_with_one_request(self):
        saved = self.client.post(
            "/api/settings/saved-chat-models",
            json={
                "model_id": "cohere/command-r",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": "delete-test-secret",
            },
        )
        assert saved.status_code == 200, saved.text

        deleted = self.client.delete(
            "/api/settings/saved-chat-models",
            params={"model_id": "cohere/command-r"},
        )
        assert deleted.status_code == 200, deleted.text
        assert deleted.json()["deleted"] is True
        assert self.client.get("/api/settings/saved-chat-models").json() == []

    def test_saved_chat_model_can_be_activated_without_changing_embedding_settings(self):
        self.client.put("/api/settings", json={"embedding_model": "old-embed"})
        self.client.post("/api/settings/saved-chat-models", json={
            "model_id": "cohere/command-r", "base_url": "https://openrouter.ai/api/v1", "api_key": "chat-use-secret",
        })
        response = self.client.post("/api/settings/saved-chat-models/use", json={"model_id": "cohere/command-r"})
        assert response.status_code == 200, response.text
        settings = self.client.get("/api/settings").json()
        assert settings["use_default_provider"] is False
        assert settings["chat_model"] == "cohere/command-r"
        assert settings["base_url"] == "https://openrouter.ai/api/v1"
        assert settings["api_key_set"] is True
        assert settings["embedding_model"] == "old-embed"
        assert "chat-use-secret" not in response.text

    def test_saved_chat_model_test_uses_saved_credentials_without_activating_it(self):
        self.client.post("/api/settings/saved-chat-models", json={
            "model_id": "cohere/command-r", "base_url": "https://openrouter.ai/api/v1", "api_key": "chat-test-secret",
        })
        with patch("app.routers.settings.llm_client.provider_diagnostics", return_value={"ok": True, "message": "Connection OK"}) as diagnostic:
            response = self.client.post("/api/settings/saved-chat-models/test", json={"model_id": "cohere/command-r"})
        assert response.status_code == 200, response.text
        assert response.json() == {"ok": True, "message": "Connection OK"}
        assert diagnostic.call_args.args[0].api_key == "chat-test-secret"
        assert self.client.get("/api/settings").json()["use_default_provider"] is True

    def test_chat_model_delete_is_scoped_to_current_user(self):
        db = self.Session()
        another_user = models.User(
            username="another-saved-model-owner",
            password_hash="test-hash",
            role=models.UserRole.user,
            is_active=True,
        )
        db.add(another_user)
        db.flush()
        db.add(models.UserSettings(user_id=another_user.id))
        db.add(models.SavedChatModel(
            user_id=another_user.id,
            model_id="other/model",
            base_url="https://example.com/v1",
            api_key="private-key",
        ))
        db.commit()
        db.close()

        response = self.client.delete(
            "/api/settings/saved-chat-models",
            params={"model_id": "other/model"},
        )
        assert response.status_code == 404
        db = self.Session()
        try:
            still_there = db.query(models.SavedChatModel).filter_by(user_id=another_user.id, model_id="other/model").first()
            assert still_there is not None
        finally:
            db.close()

    def test_missing_saved_chat_table_returns_actionable_migration_instructions(self):
        models.SavedChatModel.__table__.drop(self.engine)
        response = self.client.get("/api/settings/saved-chat-models")
        assert response.status_code == 503
        assert "013_repair_saved_model_registries.sql" in response.json()["detail"]
        assert "SQL Editor" in response.json()["detail"] or "SQL Editor" in response.text
