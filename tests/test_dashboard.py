import sys
import types
import unittest
from datetime import datetime

if "openai" not in sys.modules:
    fake_openai = types.ModuleType("openai")

    class OpenAI:  # noqa: N801
        pass

    class APIError(Exception):
        pass

    class APIConnectionError(APIError):
        pass

    class AuthenticationError(APIError):
        pass

    fake_openai.OpenAI = OpenAI
    fake_openai.APIError = APIError
    fake_openai.APIConnectionError = APIConnectionError
    fake_openai.AuthenticationError = AuthenticationError
    sys.modules["openai"] = fake_openai

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app import models
from app.main import app
from app.security import get_current_user


class DashboardSummaryTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        db = self.Session()
        user = models.User(
            username="summary-user",
            password_hash="hash",
            role=models.UserRole.user,
            is_active=True,
        )
        db.add(user)
        db.flush()
        db.add(models.UserSettings(user_id=user.id))
        db.add(models.Document(user_id=user.id, title="Doc", content="Content", created_at=datetime.utcnow()))
        db.flush()
        db.add(models.Chunk(document_id=1, user_id=user.id, chunk_index=0, text="chunk", embedding="[1,0]"))
        playground = models.ChatSession(user_id=user.id, source=models.ChatSource.playground)
        widget = models.ChatSession(user_id=user.id, source=models.ChatSource.widget)
        db.add_all([playground, widget])
        db.flush()
        db.add_all([
            models.ChatMessage(session_id=playground.id, role="user", content="hi"),
            models.ChatMessage(session_id=widget.id, role="assistant", content="hello"),
        ])
        db.commit()
        db.refresh(user)
        _ = user.settings  # eagerly load relation before detaching the fixture
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

    def tearDown(self):
        app.dependency_overrides.clear()
        self.engine.dispose()

    def test_summary_is_scoped_and_counts_sessions_and_messages(self):
        response = self.client.get("/api/dashboard/summary")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["document_count"], 1)
        self.assertEqual(body["chunk_count"], 1)
        self.assertEqual(body["playground_session_count"], 1)
        self.assertEqual(body["widget_session_count"], 1)
        self.assertEqual(body["message_count"], 2)
        self.assertEqual(body["provider_label"], "مدل رایگان آماده")
        self.assertTrue(body["widget_online"])


if __name__ == "__main__":
    unittest.main()
