import sys
import types

if "openai" not in sys.modules:
    fake_openai = types.ModuleType("openai")
    class OpenAI:  # noqa: N801
        def __init__(self, **kwargs):
            self.kwargs = kwargs
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

from app import schemas
from app.routers import settings as settings_router
from app.services import llm_client


class FakeSettings:
    use_default_provider = True
    api_key = "saved-key"
    base_url = "https://saved.example/v1"
    chat_model = "chat-old"
    embedding_model = "embed-old"


class FakeUser:
    id = 1
    settings = FakeSettings()


class AIProviderTests(unittest.TestCase):
    def test_normalize_base_url(self):
        self.assertEqual(llm_client.normalize_base_url(" https://example.com/v1/// "), "https://example.com/v1")

    def test_discovery_sorts_and_deduplicates_model_ids(self):
        fake_client = SimpleNamespace(
            models=SimpleNamespace(
                list=lambda: SimpleNamespace(
                    data=[
                        SimpleNamespace(id="z-model"),
                        SimpleNamespace(id="a-model"),
                        SimpleNamespace(id="a-model"),
                    ]
                )
            )
        )
        with patch("app.services.llm_client._client", return_value=fake_client):
            result = llm_client.list_models("https://example.com/v1///", "secret")
        self.assertEqual(result, ["a-model", "z-model"])

    def test_discovery_route_does_not_persist_form_key(self):
        payload = schemas.DiscoverModelsRequest(
            base_url="https://api.example/v1", api_key="form-secret"
        )
        with patch("app.routers.settings.llm_client.list_models", return_value=["chat-1", "embed-1"]):
            response = settings_router.discover_models(payload, FakeUser())
        self.assertEqual(response.models, ["chat-1", "embed-1"])
        self.assertEqual(FakeUser.settings.api_key, "saved-key")


    def test_client_uses_hosted_timeout_and_retry_settings(self):
        fake = SimpleNamespace()
        with patch("app.services.llm_client.OpenAI", return_value=fake) as openai_cls:
            result = llm_client._client(" https://example.com/v1/// ", "secret")
        self.assertIs(result, fake)
        kwargs = openai_cls.call_args.kwargs
        self.assertEqual(kwargs["base_url"], "https://example.com/v1")
        self.assertEqual(kwargs["api_key"], "secret")
        self.assertEqual(kwargs["timeout"], llm_client.config.AI_REQUEST_TIMEOUT_SECONDS)
        self.assertEqual(kwargs["max_retries"], llm_client.config.AI_MAX_RETRIES)

    def test_list_models_requires_key(self):
        with self.assertRaises(llm_client.LLMError):
            llm_client.list_models("https://example.com/v1", "")


if __name__ == "__main__":
    unittest.main()
