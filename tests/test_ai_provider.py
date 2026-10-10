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
    separate_embedding_provider = False
    embedding_api_key = None
    embedding_base_url = None


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
            "chat_probe_ok": True,
            "embedding_probe_ok": True,
            "dual_capable_models": [],
        }):
            response = settings_router.discover_models(payload, FakeUser())
        self.assertEqual(response.models, ["chat-1", "embed-1"])
        self.assertEqual(response.embedding_models, ["embed-1"])
        self.assertEqual(FakeUser.settings.api_key, "saved-key")


    def test_discovery_uses_form_credentials_for_unsaved_separate_embedding_provider(self):
        payload = schemas.DiscoverModelsRequest(
            base_url="https://openrouter.ai/api/v1",
            api_key="form-chat-key",
            separate_embedding_provider=True,
            embedding_base_url="https://embedding.example/v1",
            embedding_api_key="form-embedding-key",
        )
        expected = {
            "models": ["chat-model"], "chat_models": ["chat-model"],
            "embedding_models": [], "unknown_models": [],
        }
        with patch("app.routers.settings.llm_client.discover_model_capabilities", return_value=expected) as discover:
            response = settings_router.discover_models(payload, FakeUser())
        self.assertEqual(response.chat_models, ["chat-model"])
        discover.assert_called_once_with(
            "https://openrouter.ai/api/v1", "form-chat-key",
            embedding_base_url="https://embedding.example/v1",
            embedding_api_key="form-embedding-key",
        )
        # Discovery is intentionally read-only; the supplied form key is not saved.
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


    def test_resolve_provider_supports_separate_embedding_credentials(self):
        fake = FakeSettings()
        fake.use_default_provider = False
        fake.api_key = "chat-key"
        fake.base_url = "https://chat.example/v1"
        fake.separate_embedding_provider = True
        fake.embedding_api_key = "embed-key"
        fake.embedding_base_url = "https://embed.example/v1"
        provider = llm_client.resolve_provider(fake)
        self.assertEqual(provider.base_url, "https://chat.example/v1")
        self.assertEqual(provider.api_key, "chat-key")
        self.assertEqual(provider.embedding_base_url, "https://embed.example/v1")
        self.assertEqual(provider.embedding_api_key, "embed-key")


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
            chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace()]))),
        )
        with patch("app.services.llm_client._client", return_value=fake_client):
            result = llm_client.discover_model_capabilities("https://example.com/v1", "secret")
        self.assertEqual(result["chat_models"], ["chat-alpha"])
        self.assertEqual(result["embedding_models"], ["qwen3-embedding-4b"])
        self.assertEqual(result["dual_capable_models"], [])

    def test_discovery_probes_every_candidate_not_just_a_small_fixed_cap(self):
        # Regression test for the real-world OpenRouter bug report: a provider
        # that lists dozens/hundreds of models must not have discovery silently
        # stop at a small arbitrary slice (the old code capped "unknown" chat
        # candidates at 16). With the default MAX_CHAT_MODEL_PROBES (80), all
        # 40 of these legitimate chat models must come back verified.
        model_ids = [f"vendor-{i}/chat-model-{i}" for i in range(40)]
        fake_client = SimpleNamespace(
            models=SimpleNamespace(list=lambda: SimpleNamespace(
                data=[SimpleNamespace(id=mid) for mid in model_ids]
            )),
            embeddings=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(data=[])),
            chat=SimpleNamespace(completions=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace()])
            )),
        )
        with patch("app.services.llm_client._client", return_value=fake_client):
            result = llm_client.discover_model_capabilities("https://example.com/v1", "secret")
        self.assertEqual(len(result["chat_models"]), 40)
        self.assertEqual(result["total_models_found"], 40)
        self.assertFalse(result["chat_candidates_truncated"])

    def test_discovery_respects_configurable_probe_cap_and_reports_truncation(self):
        model_ids = [f"vendor/model-{i}" for i in range(5)]
        fake_client = SimpleNamespace(
            models=SimpleNamespace(list=lambda: SimpleNamespace(
                data=[SimpleNamespace(id=mid) for mid in model_ids]
            )),
            embeddings=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(data=[])),
            chat=SimpleNamespace(completions=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace()])
            )),
        )
        with patch("app.services.llm_client._client", return_value=fake_client), \
             patch.object(llm_client.config, "MAX_CHAT_MODEL_PROBES", 2):
            result = llm_client.discover_model_capabilities("https://example.com/v1", "secret")
        self.assertEqual(result["chat_candidates_probed"], 2)
        self.assertEqual(len(result["chat_models"]), 2)
        self.assertTrue(result["chat_candidates_truncated"])

    def test_discovery_uses_declared_architecture_to_skip_non_text_models(self):
        # A provider (e.g. OpenRouter) that annotates each model with
        # input/output modalities lets discovery skip obviously-irrelevant
        # models (image generators, etc.) without wasting a probe call on them,
        # and trust a declared text/embedding model without needing its name
        # to match a heuristic.
        probed_models = []

        def fake_chat_create(**kwargs):
            probed_models.append(kwargs["model"])
            return SimpleNamespace(choices=[SimpleNamespace()])

        fake_client = SimpleNamespace(
            models=SimpleNamespace(list=lambda: SimpleNamespace(data=[
                SimpleNamespace(id="vendor/text-model", architecture=SimpleNamespace(
                    output_modalities=["text"], input_modalities=["text"],
                )),
                SimpleNamespace(id="vendor/image-model", architecture=SimpleNamespace(
                    output_modalities=["image"], input_modalities=["text"],
                )),
            ])),
            embeddings=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(data=[])),
            chat=SimpleNamespace(completions=SimpleNamespace(create=fake_chat_create)),
        )
        with patch("app.services.llm_client._client", return_value=fake_client):
            result = llm_client.discover_model_capabilities("https://example.com/v1", "secret")
        self.assertEqual(result["chat_models"], ["vendor/text-model"])
        self.assertNotIn("vendor/image-model", probed_models)
        self.assertNotIn("vendor/image-model", result["unknown_models"])

    def test_discovery_merges_openrouter_specific_embedding_catalog(self):
        # OpenRouter serves embedding-capable models from a dedicated
        # /embeddings/models endpoint that is entirely separate from /models.
        # A model that only exists in that catalog must still be probed and
        # offered, even though it never appears in the general model list.
        fake_client = SimpleNamespace(
            models=SimpleNamespace(list=lambda: SimpleNamespace(data=[
                SimpleNamespace(id="vendor/chat-only"),
            ])),
            embeddings=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(
                data=[SimpleNamespace(embedding=[0.0] * llm_client.config.EMBEDDING_DIMENSIONS)]
                if kwargs["model"] == "openai/text-embedding-3-small" else []
            )),
            chat=SimpleNamespace(completions=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace()])
            )),
        )
        with patch("app.services.llm_client._client", return_value=fake_client), \
             patch("app.services.llm_client._fetch_openrouter_model_catalog", return_value=[{
                 "id": "vendor/chat-only", "name": "Chat only", "context_length": 8192,
                 "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
                 "pricing": {"prompt": "0", "completion": "0"},
             }]), \
             patch("app.services.llm_client._fetch_openrouter_embedding_catalog",
                   return_value=["openai/text-embedding-3-small"]):
            result = llm_client.discover_model_capabilities("https://openrouter.ai/api/v1", "secret")
        self.assertIn("openai/text-embedding-3-small", result["embedding_models"])
        self.assertEqual(result["chat_models"], ["vendor/chat-only"])
        self.assertEqual(result["free_chat_models_count"], 1)
        self.assertEqual(result["total_models_found"], 2)
        response_schema = schemas.DiscoverModelsResponse(**result)
        self.assertEqual(response_schema.model_catalog[0].price_tier, "free")

    def test_openrouter_lists_all_text_chat_models_with_free_and_paid_metadata_without_chat_probes(self):
        raw_catalog = [
            {
                "id": "sample/free-chat:free", "name": "Free Chat", "context_length": 32768,
                "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
                "pricing": {"prompt": "0", "completion": "0"},
            },
            {
                "id": "sample/paid-chat", "name": "Paid Chat", "context_length": 128000,
                "architecture": {"input_modalities": ["text", "image"], "output_modalities": ["text"]},
                "pricing": {"prompt": "0.000001", "completion": "0.000004"},
            },
            {
                "id": "sample/image-gen", "name": "Image Generator", "context_length": 1024,
                "architecture": {"input_modalities": ["text"], "output_modalities": ["image"]},
                "pricing": {"prompt": "0.000001", "completion": "0.001"},
            },
        ]
        fake_client = SimpleNamespace(
            embeddings=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(data=[])),
            chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: (_ for _ in ()).throw(
                AssertionError("OpenRouter discovery must not send a paid chat probe to every catalogue entry")
            ))),
        )
        with patch("app.services.llm_client._fetch_openrouter_model_catalog", return_value=raw_catalog), \
             patch("app.services.llm_client._fetch_openrouter_embedding_catalog", return_value=[]), \
             patch("app.services.llm_client._client", return_value=fake_client):
            result = llm_client.discover_model_capabilities("https://openrouter.ai/api/v1", "secret")

        self.assertEqual(result["total_models_found"], 3)
        self.assertEqual(result["chat_models"], ["sample/free-chat:free", "sample/paid-chat"])
        self.assertEqual(result["free_chat_models_count"], 1)
        self.assertEqual(result["paid_chat_models_count"], 1)
        self.assertEqual(result["chat_candidates_probed"], 0)
        catalog = {item["id"]: item for item in result["model_catalog"]}
        self.assertEqual(catalog["sample/free-chat:free"]["price_tier"], "free")
        self.assertEqual(catalog["sample/paid-chat"]["price_tier"], "paid")
        self.assertFalse(catalog["sample/image-gen"]["supports_chat"])

    def test_openrouter_embedding_is_only_selected_when_dimension_matches_project(self):
        raw_catalog = [{
            "id": "sample/chat", "name": "Chat", "architecture": {
                "input_modalities": ["text"], "output_modalities": ["text"]
            }, "pricing": {"prompt": "0", "completion": "0"},
        }]
        fake_client = SimpleNamespace(
            embeddings=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(data=[
                SimpleNamespace(embedding=[0.0] * (llm_client.config.EMBEDDING_DIMENSIONS - 1))
            ])),
            chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(choices=[]))),
        )
        with patch("app.services.llm_client._fetch_openrouter_model_catalog", return_value=raw_catalog), \
             patch("app.services.llm_client._fetch_openrouter_embedding_catalog", return_value=["openai/text-embedding-3-small"]), \
             patch("app.services.llm_client._client", return_value=fake_client):
            result = llm_client.discover_model_capabilities("https://openrouter.ai/api/v1", "secret")
        self.assertEqual(result["embedding_models"], [])
        self.assertFalse(result["embedding_probe_ok"])

    def test_openrouter_raw_catalog_keeps_metadata_and_uses_server_side_authorization(self):
        from unittest.mock import MagicMock

        payload = {"data": [{
            "id": "sample/model", "name": "Sample", "context_length": 32768,
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
            "pricing": {"prompt": "0", "completion": "0"},
        }]}
        response = SimpleNamespace(status_code=200, json=lambda: payload)
        request_client = SimpleNamespace(get=lambda url, headers: (self.assertEqual(
            url, "https://openrouter.ai/api/v1/models"), self.assertEqual(
            headers["Authorization"], "Bearer test-secret"), response)[-1])
        client_factory = MagicMock()
        client_factory.return_value.__enter__.return_value = request_client
        with patch("app.services.llm_client.httpx.Client", client_factory):
            result = llm_client._fetch_openrouter_model_catalog("https://openrouter.ai/api/v1", "test-secret")
        self.assertEqual(result[0]["name"], "Sample")
        self.assertEqual(result[0]["pricing"]["completion"], "0")
        self.assertNotIn("test-secret", repr(result))

    def test_openrouter_raw_catalog_redacts_unauthorized_error(self):
        from unittest.mock import MagicMock

        response = SimpleNamespace(status_code=401, json=lambda: self.fail("401 response body should not be parsed"))
        request_client = SimpleNamespace(get=lambda *args, **kwargs: response)
        client_factory = MagicMock()
        client_factory.return_value.__enter__.return_value = request_client
        with patch("app.services.llm_client.httpx.Client", client_factory):
            with self.assertRaises(llm_client.LLMError) as caught:
                llm_client._fetch_openrouter_model_catalog("https://openrouter.ai/api/v1", "test-secret")
        self.assertNotIn("test-secret", str(caught.exception))
        self.assertIn("کلید API", str(caught.exception))

    def test_discover_embedding_models_never_touches_chat_endpoint(self):
        def fail_if_called(**kwargs):
            raise AssertionError("discover_embedding_models must not call chat.completions.create")

        fake_client = SimpleNamespace(
            models=SimpleNamespace(list=lambda: SimpleNamespace(data=[
                SimpleNamespace(id="acme/embed-small"),
                SimpleNamespace(id="acme/chat-large"),
            ])),
            embeddings=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(
                data=[SimpleNamespace(embedding=[0.0] * llm_client.config.EMBEDDING_DIMENSIONS)]
                if kwargs["model"] == "acme/embed-small" else []
            )),
            chat=SimpleNamespace(completions=SimpleNamespace(create=fail_if_called)),
        )
        with patch("app.services.llm_client._client", return_value=fake_client):
            result = llm_client.discover_embedding_models("https://example.com/v1", "secret")
        self.assertEqual(result["embedding_models"], ["acme/embed-small"])
        self.assertEqual(result["total_models_found"], 2)

