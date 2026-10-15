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

from app import schemas, config
from app.routers.playground import battle, battle_stream


class ModelBattleTests(unittest.TestCase):
    def test_battle_uses_saved_custom_provider_alongside_builtin_model(self):
        user = SimpleNamespace(id=123)
        payload = schemas.BattleRequest(
            prompt="hello", model_a="my-personal-model", model_b="qwen-35b-a3b-instruct"
        )
        settings = SimpleNamespace(
            use_default_provider=False,
            api_key="custom-key",
            base_url="https://custom.example/v1",
            chat_model="my-personal-model",
            embedding_model="my-embedding-model",
            separate_embedding_provider=False,
            embedding_base_url=None,
            embedding_api_key=None,
        )
        providers_used = {}

        def fake_timed(messages, provider, model):
            providers_used[model] = provider.base_url
            return f"reply-{model}", 10, None

        db = SimpleNamespace(execute=lambda *_args, **_kwargs: None)
        with patch("app.routers.playground.user_settings_compat.get", return_value=settings):
            with patch("app.routers.playground.llm_client.timed_chat_completion", side_effect=fake_timed):
                result = battle(payload, user, db)

        self.assertEqual(providers_used["my-personal-model"], "https://custom.example/v1")
        self.assertEqual(providers_used["qwen-35b-a3b-instruct"], config.DEFAULT_PROVIDER_BASE_URL)
        self.assertEqual(result.side_a.model, "my-personal-model")

    def test_battle_uses_saved_model_specific_provider_profile(self):
        from app.routers.playground import _battle_provider_for_model
        saved = SimpleNamespace(base_url="https://openrouter.ai/api/v1", api_key="old-key")
        query = SimpleNamespace(filter_by=lambda **kwargs: SimpleNamespace(first=lambda: saved if kwargs == {"user_id": 44, "model_id": "cohere/command-r:free"} else None))
        db = SimpleNamespace(query=lambda _model: query)
        provider = _battle_provider_for_model("cohere/command-r:free", db=db, user_id=44)
        self.assertEqual(provider.base_url, "https://openrouter.ai/api/v1")
        self.assertEqual(provider.api_key, "old-key")
        self.assertEqual(provider.chat_model, "cohere/command-r:free")

    def test_battle_rejects_custom_model_that_is_not_saved_for_this_user(self):
        from fastapi import HTTPException
        from app.routers.playground import _battle_provider_for_model

        settings = SimpleNamespace(
            use_default_provider=False,
            api_key="custom-key",
            base_url="https://custom.example/v1",
            chat_model="saved-model",
            embedding_model="embedding-model",
            separate_embedding_provider=False,
        )
        with self.assertRaises(HTTPException) as raised:
            _battle_provider_for_model("not-saved-model", settings)
        self.assertEqual(raised.exception.status_code, 400)

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
