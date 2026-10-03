import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app import models
from app.services import rag_store


class RAGStoreTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine)
        self.db = self.Session()
        user = models.User(username="retrieval", password_hash="x")
        self.db.add(user)
        self.db.flush()
        doc = models.Document(user_id=user.id, title="Doc", content="A")
        self.db.add(doc)
        self.db.flush()
        rag_store.add_chunks(
            self.db,
            user.id,
            doc.id,
            ["high", "low"],
            [[1, 0], [0.2, 0.98]],
        )
        self.db.commit()
        self.user_id = user.id

    def tearDown(self):
        self.db.close()

    def test_similarity_threshold_removes_weak_matches(self):
        matches = rag_store.search(self.db, self.user_id, [1, 0], top_k=5, similarity_threshold=0.9)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0].text, "high")

    def test_search_keeps_descending_score_order(self):
        matches = rag_store.search(self.db, self.user_id, [1, 0], top_k=2, similarity_threshold=0)
        self.assertEqual([round(score, 3) for _, score in matches], sorted([round(score, 3) for _, score in matches], reverse=True))


if __name__ == "__main__":
    unittest.main()
