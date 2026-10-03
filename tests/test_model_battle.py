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

import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app import schemas
from app.routers.playground import battle


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


if __name__ == "__main__":
    unittest.main()
