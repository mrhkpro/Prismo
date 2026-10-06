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
        with patch("app.routers.settings.llm_client.discover_model_capabilities", return_value={
            "models": ["chat-1", "embed-1"],
            "chat_models": ["chat-1"],
            "embedding_models": ["embed-1"],
            "unknown_models": [],
            "embedding_probe_ok": True,
        }):
            response = settings_router.discover_models(payload, FakeUser())
        self.assertEqual(response.models, ["chat-1", "embed-1"])
        self.assertEqual(response.embedding_models, ["embed-1"])
        self.assertEqual(FakeUser.settings.api_key, "saved-key")


    def test_client_uses_hosted_timeout_and_retry_settings(self):
        fake = SimpleNamespace()
        with patch("app.services.llm_client.OpenAI", return_value=fake) as openai_cls:
            result = llm_client._client(" https://example.com/v1/// ", "secret")
        self.assertIs(result, fake)
        kwargs = openai_cls.call_args.kwargs
        self.assertEqual(kwargs["base_url"], "https://example.com/v1")
        self.assertEqual(kwargs["api_key"], "secret")
        self.assertEqual(kwargs["timeout"].read, llm_client.config.AI_REQUEST_TIMEOUT_SECONDS)
        self.assertEqual(kwargs["timeout"].connect, llm_client.config.AI_CONNECT_TIMEOUT_SECONDS)
        self.assertEqual(kwargs["max_retries"], llm_client.config.AI_MAX_RETRIES)

    def test_chat_completion_honors_explicit_model_and_output_cap(self):
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=lambda **kwargs: SimpleNamespace(
                        choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))]
                    )
                )
            )
        )
        provider = llm_client.ProviderConfig(
            base_url="https://example.com/v1",
            api_key="secret",
            chat_model="saved-model",
            embedding_model="embed-model",
            is_default=True,
        )
        with patch("app.services.llm_client._client", return_value=fake_client):
            with patch.object(fake_client.chat.completions, "create", wraps=fake_client.chat.completions.create) as create:
                reply = llm_client.chat_completion(
                    [{"role": "user", "content": "hello"}],
                    provider,
                    model="explicit-model",
                )
        self.assertEqual(reply, "ok")
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs["model"], "explicit-model")
        self.assertEqual(kwargs["max_tokens"], llm_client.config.AI_MAX_OUTPUT_TOKENS)

    def test_connection_uses_models_endpoint_before_inference(self):
        fake_client = SimpleNamespace(
            models=SimpleNamespace(
                list=lambda: SimpleNamespace(
                    data=[SimpleNamespace(id="selected-model")]
                )
            )
        )
        provider = llm_client.ProviderConfig(
            base_url="https://example.com/v1",
            api_key="secret",
            chat_model="selected-model",
            embedding_model="embed-model",
            is_default=True,
        )
        with patch("app.services.llm_client._client", return_value=fake_client):
            ok, message = llm_client.test_connection(provider)
        self.assertTrue(ok)
        self.assertIn("موفقیت", message)

    def test_list_models_requires_key(self):
        with self.assertRaises(llm_client.LLMError):
            llm_client.list_models("https://example.com/v1", "")


if __name__ == "__main__":
    unittest.main()

class ProviderDiagnosticsTests(unittest.TestCase):
    def test_connection_error_exposes_stage_without_api_key(self):
        from openai import APIConnectionError
        exc = APIConnectionError("connect failed")
        exc.__cause__ = OSError("[Errno -2] Name or service not known")
        provider = llm_client.ProviderConfig(
            base_url="https://racode.example/v1",
            api_key="VERY-SECRET-KEY",
            chat_model="chat-model",
            embedding_model="embed-model",
            is_default=True,
        )
        message = llm_client.format_provider_error(exc, provider, operation="chat")
        self.assertIn("مرحله: dns", message)
        self.assertIn("racode.example", message)
        self.assertNotIn("VERY-SECRET-KEY", message)

    def test_provider_diagnostics_falls_back_to_chat_when_models_missing(self):
        fake_client = SimpleNamespace(
            models=SimpleNamespace(
                list=lambda: (_ for _ in ()).throw(type("E", (Exception,), {"status_code": 404})())
            ),
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=lambda **kwargs: SimpleNamespace()
                )
            ),
        )
        provider = llm_client.ProviderConfig(
            base_url="https://example.com/v1",
            api_key="secret",
            chat_model="selected-model",
            embedding_model="embed-model",
            is_default=True,
        )
        with patch("app.services.llm_client._client", return_value=fake_client):
            result = llm_client.provider_diagnostics(provider)
        self.assertTrue(result["ok"])
        self.assertEqual(result["stage"], "chat_probe")

class ProviderRelayTests(unittest.TestCase):
    def test_default_provider_uses_relay_when_configured(self):
        with patch.object(llm_client.config, "AI_PROXY_BASE_URL", "https://relay.example/v1"), \
             patch.object(llm_client.config, "AI_PROXY_API_KEY", "relay-key"):
            provider = llm_client.resolve_provider(FakeSettings())
        self.assertEqual(provider.base_url, "https://relay.example/v1")
        self.assertEqual(provider.api_key, "relay-key")
        self.assertTrue(provider.is_default)

    def test_direct_default_provider_remains_fallback_without_relay(self):
        with patch.object(llm_client.config, "AI_PROXY_BASE_URL", ""), \
             patch.object(llm_client.config, "AI_PROXY_API_KEY", ""), \
             patch.object(llm_client.config, "DEFAULT_PROVIDER_BASE_URL", "https://direct.example/v1"), \
             patch.object(llm_client.config, "DEFAULT_PROVIDER_API_KEY", "direct-key"):
            provider = llm_client.resolve_provider(FakeSettings())
        self.assertEqual(provider.base_url, "https://direct.example/v1")
        self.assertEqual(provider.api_key, "direct-key")


class ProviderCapabilityTests(unittest.TestCase):
    def test_discovery_separates_verified_embedding_models(self):
        fake_client = SimpleNamespace(
            models=SimpleNamespace(list=lambda: SimpleNamespace(data=[
                SimpleNamespace(id="chat-alpha"),
                SimpleNamespace(id="qwen3-embedding-4b"),
            ])),
            embeddings=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(
                data=[SimpleNamespace(embedding=[0.0] * llm_client.config.EMBEDDING_DIMENSIONS)]
                if kwargs["model"] == "qwen3-embedding-4b" else []
            )),
        )
        with patch("app.services.llm_client._client", return_value=fake_client):
            result = llm_client.discover_model_capabilities("https://example.com/v1", "secret")
        self.assertEqual(result["chat_models"], ["chat-alpha", "qwen3-embedding-4b"])
        self.assertEqual(result["embedding_models"], ["qwen3-embedding-4b"])

