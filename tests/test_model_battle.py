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

import asyncio
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app import schemas
from app.routers.playground import battle, battle_stream


class ModelBattleTests(unittest.TestCase):
    def test_models_are_called_concurrently(self):
        calls = []

        def fake_timed(messages, provider, model):
            calls.append(model)
            time.sleep(0.15)
            return f"reply-{model}", 150, None

        user = SimpleNamespace(id=1)
        payload = schemas.BattleRequest(prompt="hello", model_a="qwen-35b-a3b-instruct", model_b="deepseek-v4-flash-instruct")
        started = time.perf_counter()
        with patch("app.routers.playground.llm_client.timed_chat_completion", side_effect=fake_timed):
            result = battle(payload, user)
        elapsed = time.perf_counter() - started

        self.assertCountEqual(calls, [payload.model_a, payload.model_b])
        self.assertLess(elapsed, 0.28)
        self.assertEqual(result.side_a.reply, f"reply-{payload.model_a}")
        self.assertEqual(result.side_b.reply, f"reply-{payload.model_b}")

    def test_streaming_battle_emits_tokens_for_both_models_concurrently(self):
        user = SimpleNamespace(id=1)
        payload = schemas.BattleRequest(prompt="hello", model_a="qwen-35b-a3b-instruct", model_b="deepseek-v4-flash-instruct")

        def fake_stream(messages, provider, model):
            yield f"{model}-"
            time.sleep(0.02)
            yield "reply"

        async def read_body(response):
            parts = []
            async for part in response.body_iterator:
                parts.append(part.decode("utf-8") if isinstance(part, bytes) else part)
            return "".join(parts)

        with patch("app.routers.playground.llm_client.stream_chat_completion", side_effect=fake_stream):
            response = battle_stream(payload, user)
            body = asyncio.run(read_body(response))

        self.assertEqual(response.media_type, "text/event-stream")
        self.assertIn('event: meta', body)
        self.assertIn('"side": "a"', body)
        self.assertIn('"side": "b"', body)
        self.assertIn('"t": "qwen-35b-a3b-instruct-"', body)
        self.assertIn('"t": "deepseek-v4-flash-instruct-"', body)
        self.assertIn('event: side_done', body)
        self.assertIn('event: done', body)

    def test_streaming_battle_keeps_one_model_error_isolated(self):
        user = SimpleNamespace(id=1)
        payload = schemas.BattleRequest(prompt="hello", model_a="qwen-35b-a3b-instruct", model_b="deepseek-v4-flash-instruct")

        def fake_stream(messages, provider, model):
            if model == payload.model_a:
                raise RuntimeError("model A unavailable")
            yield "healthy answer"

        async def read_body(response):
            parts = []
            async for part in response.body_iterator:
                parts.append(part.decode("utf-8") if isinstance(part, bytes) else part)
            return "".join(parts)

        with patch("app.routers.playground.llm_client.stream_chat_completion", side_effect=fake_stream):
            body = asyncio.run(read_body(battle_stream(payload, user)))

        self.assertIn("model A unavailable", body)
        self.assertIn("healthy answer", body)
        self.assertIn('"side": "b"', body)


if __name__ == "__main__":
    unittest.main()
