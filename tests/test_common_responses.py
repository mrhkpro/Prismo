import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services import rag_pipeline
from app.services.common_responses import get_common_response


class CommonResponseTests(unittest.TestCase):
    def test_common_messages_have_instant_replies(self):
        self.assertIn("سلام", get_common_response("سلام!"))
        self.assertIn("خوبم", get_common_response("حالت چطوره؟"))
        self.assertIn("خواهش", get_common_response("ممنون"))

    def test_non_common_questions_still_use_rag(self):
        self.assertIsNone(get_common_response("قوانين نامگذاری متغیرها در پایتون چیست؟"))

    def test_rag_prepare_skips_embedding_for_common_message(self):
        settings = SimpleNamespace(chat_model="model", temperature=0.7)
        owner = SimpleNamespace(settings=settings)
        session = SimpleNamespace(messages=[])
        with patch.object(rag_pipeline.llm_client, "embed_text", side_effect=AssertionError("should not embed")):
            plan = rag_pipeline.prepare_rag_chat(None, owner, session, "حالت چطوره؟")
        self.assertTrue(plan.instant_reply)
        self.assertEqual(plan.matches, [])


if __name__ == "__main__":
    unittest.main()
