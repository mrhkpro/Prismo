import sys
import types
import unittest
from unittest.mock import patch

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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.exceptions import LLMError
from app.database import Base
from app.routers.knowledge import reindex_document, create_document


class KnowledgeReindexTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine)
        self.db = self.Session()
        self.user = models.User(username="owner", password_hash="hash")
        self.db.add(self.user)
        self.db.flush()
        self.settings = models.UserSettings(user_id=self.user.id)
        self.db.add(self.settings)
        self.doc = models.Document(user_id=self.user.id, title="Doc", content="Original")
        self.db.add(self.doc)
        self.db.flush()
        self.db.add(models.Chunk(document_id=self.doc.id, user_id=self.user.id, chunk_index=0, text="old", embedding="[1,0]"))
        self.db.commit()
        self.db.refresh(self.doc)

    def tearDown(self):
        self.db.close()

    def test_reindex_replaces_existing_chunks(self):
        def fake_index(db, user, doc):
            db.add(models.Chunk(document_id=doc.id, user_id=user.id, chunk_index=0, text="new", embedding="[1,0]"))
            db.flush()

        with patch("app.routers.knowledge._index_document", side_effect=fake_index):
            result = reindex_document(self.doc.id, self.user, self.db)
        self.assertEqual(result.chunk_count, 1)
        texts = [c.text for c in self.db.query(models.Chunk).filter(models.Chunk.document_id == self.doc.id).all()]
        self.assertEqual(texts, ["new"])


    def test_create_keeps_document_when_embedding_service_is_down(self):
        with patch("app.routers.knowledge._index_document", side_effect=LLMError("embedding unavailable")):
            result = create_document(
                type("Payload", (), {"title": "Saved", "content": "content"})(),
                self.user,
                self.db,
            )
        self.assertEqual(result.title, "Saved")
        self.assertEqual(result.chunk_count, 0)
        stored = self.db.query(models.Document).filter(models.Document.id == result.id).one()
        self.assertEqual(stored.content, "content")

    def test_reindex_does_not_access_another_users_document(self):
        other = models.User(username="other", password_hash="hash")
        self.db.add(other)
        self.db.commit()
        with self.assertRaises(Exception):
            reindex_document(self.doc.id, other, self.db)


if __name__ == "__main__":
    unittest.main()
