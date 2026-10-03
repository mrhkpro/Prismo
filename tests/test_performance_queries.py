import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base
from app.routers.admin import list_users
from app.routers.knowledge import list_documents


class QueryPerformanceTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine)
        self.db = self.Session()
        self.user = models.User(username="perf-user", password_hash="x")
        self.db.add(self.user)
        self.db.flush()
        self.db.add(models.UserSettings(user_id=self.user.id))
        doc = models.Document(user_id=self.user.id, title="Doc", content="content")
        self.db.add(doc)
        self.db.flush()
        self.db.add_all([
            models.Chunk(document_id=doc.id, user_id=self.user.id, chunk_index=0, text="a", embedding="[1,0]"),
            models.Chunk(document_id=doc.id, user_id=self.user.id, chunk_index=1, text="b", embedding="[0,1]"),
            models.ChatSession(user_id=self.user.id, source=models.ChatSource.playground),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.db.bind.dispose()

    def test_document_list_reports_chunk_count_without_changing_contract(self):
        docs = list_documents(self.user, self.db)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].chunk_count, 2)

    def test_admin_user_list_reports_counts_in_single_result_shape(self):
        users = list_users(search=None, limit=10, offset=0, db=self.db, _admin=None)
        row = next(u for u in users if u.username == "perf-user")
        self.assertEqual(row.document_count, 1)
        self.assertEqual(row.session_count, 1)


if __name__ == "__main__":
    unittest.main()
