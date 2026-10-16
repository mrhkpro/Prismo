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


class RAGPerformanceContractTests(unittest.TestCase):
    def test_chat_pipeline_retries_unreadable_mixed_script_model_output(self):
        settings = SimpleNamespace(
            chat_model="saved-model", embedding_model="embed", system_prompt="System",
            temperature=0.7, top_k=4, similarity_threshold=0.0,
        )
        owner = SimpleNamespace(id=7, settings=settings)
        session = SimpleNamespace(messages=[])
        provider = SimpleNamespace(chat_model="saved-model")
        chunk = SimpleNamespace(text="Context", document=SimpleNamespace(title="Doc"))
        noise = ("فارسی " * 18) + ("calculation deployment model " * 14) + ("中文字符 " * 12) + ("русский текст " * 10) + ("한국어 문장 " * 8) + ("ภาษาไทย " * 8)
        corrected = "این پاسخ قابل‌خواندن است و سؤال را به فارسی توضیح می‌دهد."

        with patch.object(rag_pipeline.llm_client, "resolve_provider", return_value=provider), \
             patch.object(rag_pipeline.llm_client, "embed_text", return_value=[0.1]), \
             patch.object(rag_pipeline.rag_store, "search", return_value=[(chunk, 0.9)]), \
             patch.object(rag_pipeline.llm_client, "chat_completion", side_effect=[noise, corrected]) as completion:
            reply, matches = rag_pipeline.run_rag_chat(
                SimpleNamespace(), owner, session, "ساعت کاری چیست؟", model="explicit-model", language="fa"
            )

        self.assertEqual(reply, corrected)
        self.assertEqual(matches, [(chunk, 0.9)])
        self.assertEqual(completion.call_count, 2)
        self.assertLessEqual(completion.call_args.kwargs["temperature"], 0.2)

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
                SimpleNamespace(), owner, session, "ساعت کاری چیست؟", model="explicit-model"
            )

        self.assertEqual(reply, "reply")
        self.assertEqual(matches, [(chunk, 0.9)])
        log_info.assert_called_once()
        self.assertIn("explicit-model", log_info.call_args.args[1:])


if __name__ == "__main__":
    unittest.main()

class FastLabModeTests(unittest.TestCase):
    def test_fast_lab_uses_smaller_context_history_and_output_budget(self):
        settings = SimpleNamespace(
            chat_model="saved-model", embedding_model="embed", system_prompt="System",
            temperature=0.7, top_k=4, similarity_threshold=0.0,
        )
        owner = SimpleNamespace(id=11, settings=settings)
        history = [
            SimpleNamespace(role=("user" if i % 2 == 0 else "assistant"), content=f"history-{i}")
            for i in range(10)
        ]
        session = SimpleNamespace(id="s1", user_id=11, messages=history)
        provider = SimpleNamespace(chat_model="saved-model", base_url="https://api.example.test/v1")
        chunks = [
            (SimpleNamespace(text=(f"context-{i} " + "x" * 1500), document=SimpleNamespace(title=f"Doc {i}")), 0.9 - i / 10)
            for i in range(4)
        ]
        with patch.object(rag_pipeline.injection_scanner, "scan", return_value=(False, None)), \
             patch.object(rag_pipeline.answer_cache, "find_historical_answer", return_value=None), \
             patch.object(rag_pipeline.llm_client, "resolve_provider", return_value=provider), \
             patch.object(rag_pipeline.llm_client, "embed_text", return_value=[0.1]), \
             patch.object(rag_pipeline.rag_store, "search", return_value=chunks):
            plan = rag_pipeline.prepare_rag_chat(
                SimpleNamespace(), owner, session, "این سند درباره چیست؟", fast_mode=True,
            )

        self.assertTrue(plan.fast_mode)
        self.assertLessEqual(plan.max_output_tokens, rag_pipeline.FAST_LAB_MAX_OUTPUT_TOKENS)
        self.assertLessEqual(len(plan.messages) - 2, rag_pipeline.FAST_LAB_HISTORY_MESSAGES)
        system_message = plan.messages[0]["content"]
        self.assertIn("مستقیم و کوتاه پاسخ بده", system_message)
        context_start = system_message.index("--- دانشنامه")
        context = system_message[context_start:]
        self.assertLessEqual(len(context), rag_pipeline.FAST_LAB_CONTEXT_CHARS + 150)

    def test_fast_lab_does_not_spend_another_generation_retrying_noisy_text(self):
        settings = SimpleNamespace(
            chat_model="saved-model", embedding_model="embed", system_prompt="System",
            temperature=0.7, top_k=4, similarity_threshold=0.0,
        )
        owner = SimpleNamespace(id=11, settings=settings)
        session = SimpleNamespace(id="s1", user_id=11, messages=[])
        provider = SimpleNamespace(chat_model="saved-model", base_url="https://api.example.test/v1")
        chunk = SimpleNamespace(text="Context", document=SimpleNamespace(title="Doc"))
        noise = ("فارسی " * 18) + ("deployment calculation " * 30) + ("中文字符 " * 12) + ("русский текст " * 10)
        with patch.object(rag_pipeline.injection_scanner, "scan", return_value=(False, None)), \
             patch.object(rag_pipeline.answer_cache, "find_historical_answer", return_value=None), \
             patch.object(rag_pipeline.llm_client, "resolve_provider", return_value=provider), \
             patch.object(rag_pipeline.llm_client, "embed_text", return_value=[0.1]), \
             patch.object(rag_pipeline.rag_store, "search", return_value=[(chunk, 0.9)]), \
             patch.object(rag_pipeline.llm_client, "chat_completion", return_value=noise) as completion:
            reply, _ = rag_pipeline.run_rag_chat(
                SimpleNamespace(), owner, session, "سند درباره چیست؟", language="fa", fast_mode=True,
            )
        self.assertIn("مدل پاسخ قابل‌خواندن نداد", reply)
        completion.assert_called_once()

    def test_openrouter_reasoning_effort_is_lowered_only_for_fast_lab(self):
        provider = SimpleNamespace(base_url="https://openrouter.ai/api/v1")
        self.assertEqual(
            rag_pipeline.llm_client._fast_reasoning_kwargs(provider, "deepseek-v4-flash-reasoning", True),
            {"extra_body": {"reasoning": {"effort": "low", "max_tokens": 96}}},
        )
        self.assertEqual(
            rag_pipeline.llm_client._fast_reasoning_kwargs(provider, "deepseek-v4-flash-reasoning", False),
            {},
        )
        non_openrouter = SimpleNamespace(base_url="https://api.example.test/v1")
        self.assertEqual(
            rag_pipeline.llm_client._fast_reasoning_kwargs(non_openrouter, "deepseek-v4-flash-reasoning", True),
            {},
        )
