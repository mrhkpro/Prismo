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
from types import SimpleNamespace
from unittest.mock import patch

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
            {"role": "user", "content": "a" * 4000},
            {"role": "assistant", "content": "b" * 4000},
        ]
        messages = rag_pipeline.build_messages("System", "Context", history, "Q")
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[1]["role"], "assistant")


if __name__ == "__main__":
    unittest.main()


class RAGPerformanceContractTests(unittest.TestCase):
    def test_chat_pipeline_logs_timing_with_selected_model(self):
        settings = SimpleNamespace(
            chat_model="saved-model",
            embedding_model="embed",
            system_prompt="System",
            temperature=0.7,
            top_k=4,
            similarity_threshold=0.0,
        )
        owner = SimpleNamespace(id=7, settings=settings)
        session = SimpleNamespace(messages=[])
        provider = SimpleNamespace(chat_model="saved-model")
        chunk = SimpleNamespace(text="Context", document=SimpleNamespace(title="Doc"))

        with patch.object(rag_pipeline.llm_client, "resolve_provider", return_value=provider), \
             patch.object(rag_pipeline.llm_client, "embed_text", return_value=[0.1]), \
             patch.object(rag_pipeline.rag_store, "search", return_value=[(chunk, 0.9)]), \
             patch.object(rag_pipeline.llm_client, "chat_completion", return_value="reply"), \
             patch.object(rag_pipeline.logger, "info") as log_info:
            reply, matches = rag_pipeline.run_rag_chat(
                SimpleNamespace(), owner, session, "hello", model="explicit-model"
            )

        self.assertEqual(reply, "reply")
        self.assertEqual(matches, [(chunk, 0.9)])
        log_info.assert_called_once()
        self.assertIn("explicit-model", log_info.call_args.args[1:])


if __name__ == "__main__":
    unittest.main()
