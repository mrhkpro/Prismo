import sys
import types

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

import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base
from app.routers.playground import delete_session


class ChatSessionCleanupTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.user = models.User(username="chat-user", password_hash="hash")
        other = models.User(username="other-chat-user", password_hash="hash")
        self.db.add_all([self.user, other])
        self.db.flush()
        self.session = models.ChatSession(user_id=self.user.id, source=models.ChatSource.playground)
        self.db.add(self.session)
        self.db.commit()
        self.db.refresh(self.session)
        self.other = other

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_owner_can_delete_playground_session(self):
        session_id = self.session.id
        delete_session(session_id, self.user, self.db)
        self.assertIsNone(self.db.get(models.ChatSession, session_id))

    def test_other_user_cannot_delete_session(self):
        with self.assertRaises(HTTPException) as caught:
            delete_session(self.session.id, self.other, self.db)
        self.assertEqual(caught.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
