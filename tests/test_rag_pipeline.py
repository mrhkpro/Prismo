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

from app.services import rag_pipeline


class RAGPipelineTests(unittest.TestCase):
    def test_build_messages_puts_rag_context_in_explicit_delimiters(self):
        messages = rag_pipeline.build_messages("System", "[منبع 1] Data", [], "Question")
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("محتوای بازیابی‌شده", messages[0]["content"])
        self.assertIn("--- پایان دانشنامه ---", messages[0]["content"])
        self.assertEqual(messages[-1], {"role": "user", "content": "Question"})

    def test_history_is_limited_by_character_budget(self):
        history = [
            {"role": "user", "content": "a" * 8000},
            {"role": "assistant", "content": "b" * 8000},
        ]
        messages = rag_pipeline.build_messages("System", "Context", history, "Q")
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[1]["role"], "assistant")


if __name__ == "__main__":
    unittest.main()
