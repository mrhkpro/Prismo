"""
لایه‌ی ارتباط با سرویس هوش مصنوعی (هر سرویس سازگار با OpenAI API).

اگر کاربر تنظیمات اختصاصی خودش (Base URL + API Key) را وارد نکرده باشد یا
صراحتاً «استفاده از مدل رایگان آماده» را فعال گذاشته باشد، از ارائه‌دهنده‌ی
پیش‌فرض تعریف‌شده در config استفاده می‌شود.
"""
import logging
import socket
import time
from urllib.parse import urlparse
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional, Tuple

import httpx

from ..exceptions import LLMError

from openai import OpenAI, APIError, APIConnectionError, AuthenticationError

from .. import config, models

logger = logging.getLogger("prismo.llm")


@dataclass
class ProviderConfig:
    base_url: str
    api_key: str
    chat_model: str
    embedding_model: str
    is_default: bool
    embedding_base_url: Optional[str] = None
    embedding_api_key: Optional[str] = None


def resolve_provider(settings: models.UserSettings) -> ProviderConfig:
    """Resolve chat and embedding providers independently, with legacy fallback."""
    default_base = config.AI_PROXY_BASE_URL or config.DEFAULT_PROVIDER_BASE_URL
    default_key = config.AI_PROXY_API_KEY or config.DEFAULT_PROVIDER_API_KEY

    custom_chat_available = bool((getattr(settings, "base_url", None) or "").strip() and getattr(settings, "api_key", None))
    chat_is_default = bool(getattr(settings, "use_default_provider", True)) or not custom_chat_available
    if chat_is_default:
        chat_base, chat_key = default_base, default_key
    else:
        chat_base, chat_key = settings.base_url, settings.api_key

    # Existing rows predate the independent mode; retain their old "both use
    # the same mode" behavior until migration 005 stores an explicit choice.
    embedding_mode = getattr(settings, "embedding_use_default_provider", None)
    embedding_is_default = chat_is_default if embedding_mode is None else bool(embedding_mode)
    if embedding_is_default:
        embedding_base, embedding_key = default_base, default_key
    elif bool(getattr(settings, "separate_embedding_provider", False)) and getattr(settings, "embedding_base_url", None):
        embedding_base = settings.embedding_base_url
        embedding_key = getattr(settings, "embedding_api_key", None) or (chat_key if not chat_is_default else "")
    elif not chat_is_default:
        # A custom embedding may intentionally share the custom chat endpoint/key.
        embedding_base, embedding_key = chat_base, chat_key
    else:
        # Invalid/incomplete custom embedding configuration degrades to the
        # ready provider rather than causing unrelated chat requests to fail.
        embedding_base, embedding_key = default_base, default_key
        embedding_is_default = True

    return ProviderConfig(
        base_url=chat_base,
        api_key=chat_key,
        chat_model=getattr(settings, "chat_model", None) or config.DEFAULT_CHAT_MODEL,
        embedding_model=getattr(settings, "embedding_model", None) or config.DEFAULT_EMBEDDING_MODEL,
        is_default=chat_is_default,
        embedding_base_url=embedding_base,
        embedding_api_key=embedding_key,
    )


def normalize_base_url(base_url: str) -> str:
    """URL ورودی سرویس سفارشی را برای SDK یکدست می‌کند، بدون تغییر مسیر endpoint."""
    return (base_url or "").strip().rstrip("/")



def _fast_reasoning_kwargs(provider: ProviderConfig, model: str, enabled: bool) -> dict:
    """Request low reasoning effort only for reasoning models routed through OpenRouter.

    Battle and general chat retain provider defaults. The RAG lab uses this option
    because its goal is a fast, practical answer grounded in retrieved documents.
    """
    if not enabled or "openrouter.ai" not in normalize_base_url(getattr(provider, "base_url", "")).lower():
        return {}
    name = (model or "").lower()
    is_reasoning = any(token in name for token in (
        "reasoning", "thinking", "deepseek-r1", "qwq", "/o1", "/o3", "/o4",
    ))
    return {"extra_body": {"reasoning": {"effort": "low"}}} if is_reasoning else {}

@lru_cache(maxsize=16)
def _cached_client(base_url: str, api_key: str) -> OpenAI:
    """Reuse warm OpenAI-compatible clients across requests in the same runtime."""
    timeout = httpx.Timeout(
        config.AI_REQUEST_TIMEOUT_SECONDS,
        connect=config.AI_CONNECT_TIMEOUT_SECONDS,
    )
    return OpenAI(
        base_url=base_url,
        api_key=api_key,
        timeout=timeout,
        max_retries=config.AI_MAX_RETRIES,
    )


@lru_cache(maxsize=16)
def _cached_probe_client(base_url: str, api_key: str) -> OpenAI:
    """Short-timeout, no-retry client used only for model-discovery probes.

    Discovery may need to probe dozens of candidate models (large catalogs
    such as OpenRouter list hundreds). Reusing the long-lived AI_REQUEST
    timeout here would let a single slow/hanging model stall a whole probe
    batch; a short dedicated timeout keeps discovery fast and bounded.
    """
    timeout = httpx.Timeout(
        config.MODEL_PROBE_TIMEOUT_SECONDS,
        connect=config.MODEL_PROBE_CONNECT_TIMEOUT_SECONDS,
    )
    return OpenAI(
        base_url=base_url,
        api_key=api_key,
        timeout=timeout,
        max_retries=0,
    )


def _client(base_url: str, api_key: str, *, short_timeout: bool = False) -> OpenAI:
    """Create/reuse an OpenAI-compatible client with serverless-friendly timeouts.

    short_timeout=True returns the probe-tuned client (see _cached_probe_client).
    """
    normalized = normalize_base_url(base_url)
    if not normalized:
        raise LLMError("آدرس سرویس (Base URL) را وارد کنید.")
    if not api_key:
        raise LLMError("API Key سرویس را وارد کنید.")
    if short_timeout:
        return _cached_probe_client(normalized, api_key)
    return _cached_client(normalized, api_key)



_EMBEDDING_NAME_HINTS = (
    "embedding", "embed", "text-embedding", "bge", "e5-", "e5_", "gte-", "gte_",
    "jina-embeddings", "nomic-embed", "mxbai-embed", "arctic-embed", "snowflake-arctic-embed",
    "multilingual-e5", "voyage-", "cohere-embed", "uae-large-v1",
    # Gateways such as OpenRouter re-slug embedding models per-vendor; cover the
    # identifiers that actually show up in the wild so they are not missed.
    "mistral-embed", "qwen-embedding", "gte-qwen", "nv-embed",
    "embed-english", "embed-multilingual", "amazon-embeddings",
    "granite-embedding", "stella_en", "stella-en", "gemini-embedding",
    "models/embedding", "text-embedding-3", "text-embedding-ada", "embedding-001",
    "embedding-gecko", "all-minilm", "paraphrase-multilingual",
)

# Name hints for models that are clearly not text-chat/text-embedding (image,
# audio, moderation, rerank...). These never hard-exclude a candidate — a
# provider's naming can be unreliable — they only push a candidate to the
# back of the probe queue so a limited probe budget is spent on the models
# most likely to actually answer chat requests first.
_NON_TEXT_OUTPUT_HINTS = (
    "dall-e", "dalle", "stable-diffusion", "stablediffusion", "midjourney",
    "flux", "sdxl", "imagen", "whisper", "-tts", "/tts", "text-to-speech",
    "speech-to-text", "transcribe", "moderation", "rerank", "image-gen",
    "/image", "-image", "video-gen", "sora", "/video", ":free-image",
)


def _looks_like_embedding_model(model_id: str) -> bool:
    value = (model_id or "").strip().casefold()
    return any(hint in value for hint in _EMBEDDING_NAME_HINTS)


def _looks_non_text_output(model_id: str) -> bool:
    value = (model_id or "").strip().casefold()
    return any(hint in value for hint in _NON_TEXT_OUTPUT_HINTS)


def _dedup_keep_order(*groups: List[str]) -> List[str]:
    seen: set[str] = set()
    result: list[str] = []
    for group in groups:
        for item in group:
            if item not in seen:
                seen.add(item)
                result.append(item)
    return result


def _field(item, name: str, default=None):
    """Read a field from either an SDK model object or a JSON dictionary."""
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default) if item is not None else default


def _architecture_info(item) -> Optional[dict]:
    """Best-effort read of OpenRouter-style architecture metadata.

    Works with both OpenAI SDK model instances and OpenRouter's raw JSON
    records so the UI can use the full, provider-defined catalogue.
    """
    arch = _field(item, "architecture")
    if arch is None:
        return None
    try:
        output = _field(arch, "output_modalities", None) or []
        input_ = _field(arch, "input_modalities", None) or []
        modality = str(_field(arch, "modality", "") or "")
        if modality and "->" in modality and (not input_ or not output):
            left, right = modality.split("->", 1)
            if not input_:
                input_ = [part.strip() for part in left.replace(",", "+").split("+") if part.strip()]
            if not output:
                output = [part.strip() for part in right.replace(",", "+").split("+") if part.strip()]
        return {
            "output_modalities": {str(m).strip().casefold() for m in output},
            "input_modalities": {str(m).strip().casefold() for m in input_},
        }
    except Exception:
        return None


def _classify_by_architecture(architecture: Optional[dict]) -> str:
    """Return 'embedding' | 'chat' | 'excluded' | 'unknown' from declared modalities."""
    if not architecture:
        return "unknown"
    outputs = architecture.get("output_modalities") or set()
    if not outputs:
        return "unknown"
    if "embeddings" in outputs or "embedding" in outputs:
        return "embedding"
    if "text" in outputs:
        return "chat"
    # The provider explicitly declared this model's only outputs are
    # something else (image/audio/video/rerank/...); it cannot serve chat
    # or embedding requests, so skip probing it entirely.
    return "excluded"


def _is_openrouter_host(base_url: str) -> bool:
    try:
        host = (urlparse(base_url).netloc or "").lower()
    except Exception:
        return False
    return host == "openrouter.ai" or host.endswith(".openrouter.ai")


def _fetch_openrouter_model_catalog(base_url: str, api_key: str) -> List[dict]:
    """Fetch the complete OpenRouter model catalogue, including pricing.

    Unlike the OpenAI-compatible ``/models`` wrapper, this direct request
    retains OpenRouter-specific name, modality, context-length, and pricing
    metadata. API keys and response bodies are deliberately excluded from
    diagnostic errors.
    """
    if not _is_openrouter_host(base_url):
        return []
    if not api_key:
        raise LLMError("برای دریافت کاتالوگ OpenRouter باید API Key وارد شود.")
    parsed = urlparse(base_url)
    path = parsed.path.rstrip("/") or "/api/v1"
    url = f"{parsed.scheme}://{parsed.netloc}{path}/models"
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    app_url = str(getattr(config, "APP_PUBLIC_URL", "") or "").strip()
    if app_url.startswith(("https://", "http://")):
        headers["HTTP-Referer"] = app_url
    headers["X-Title"] = "Prismo"
    try:
        with httpx.Client(timeout=httpx.Timeout(
            config.MODEL_PROBE_TIMEOUT_SECONDS,
            connect=config.MODEL_PROBE_CONNECT_TIMEOUT_SECONDS,
        )) as http_client:
            response = http_client.get(url, headers=headers)
        if response.status_code in (401, 403):
            raise LLMError("OpenRouter کلید API را نپذیرفت؛ معتبر بودن کلید و دسترسی حساب را بررسی کنید.")
        if response.status_code == 429:
            raise LLMError("OpenRouter محدودیت درخواست اعمال کرد؛ کمی بعد دوباره تلاش کنید.")
        if response.status_code >= 400:
            raise LLMError(f"دریافت فهرست مدل‌های OpenRouter با خطای HTTP {response.status_code} ناموفق بود.")
        payload = response.json()
        entries = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(entries, list):
            raise LLMError("پاسخ کاتالوگ OpenRouter ساختار قابل‌شناسایی نداشت.")
        return [entry for entry in entries if isinstance(entry, dict) and str(entry.get("id") or "").strip()]
    except LLMError:
        raise
    except httpx.TimeoutException as exc:
        raise LLMError("مهلت دریافت کاتالوگ OpenRouter تمام شد؛ اتصال شبکه را بررسی کنید.") from exc
    except httpx.HTTPError as exc:
        raise LLMError("ارتباط با کاتالوگ OpenRouter برقرار نشد؛ شبکه و Base URL را بررسی کنید.") from exc
    except (ValueError, TypeError) as exc:
        raise LLMError("پاسخ کاتالوگ OpenRouter قابل‌خواندن نبود.") from exc


def _as_float(value) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _openrouter_catalog_entry(item: dict, embedding_ids: Optional[set[str]] = None) -> dict:
    """Normalize provider metadata for the API/UI without dropping models."""
    model_id = str(item.get("id") or "").strip()
    name = str(item.get("name") or model_id)
    architecture = _architecture_info(item) or {}
    inputs = sorted(architecture.get("input_modalities") or set())
    outputs = sorted(architecture.get("output_modalities") or set())
    price = item.get("pricing") if isinstance(item.get("pricing"), dict) else {}
    prompt_price = _as_float(price.get("prompt"))
    completion_price = _as_float(price.get("completion"))
    model_id_lower = model_id.casefold()
    if model_id_lower.endswith(":free") or (prompt_price == 0 and completion_price == 0):
        price_tier = "free"
    elif (prompt_price is not None and prompt_price > 0) or (completion_price is not None and completion_price > 0):
        price_tier = "paid"
    else:
        price_tier = "unknown"

    if "text" in outputs and ("text" in inputs or not inputs):
        supports_chat = True
    elif outputs and "text" not in outputs:
        supports_chat = False
    elif inputs and "text" not in inputs:
        supports_chat = False
    else:
        # The catalogue sometimes omits modality metadata for newer models.
        # Be inclusive in that case, but avoid obvious embedding/image/audio IDs.
        supports_chat = not _looks_like_embedding_model(model_id) and not _looks_non_text_output(model_id)

    declared_embedding = bool({"embedding", "embeddings"} & set(outputs))
    supports_embeddings = declared_embedding or model_id in (embedding_ids or set()) or _looks_like_embedding_model(model_id)
    context = item.get("context_length")
    try:
        context = int(context) if context is not None else None
    except (TypeError, ValueError):
        context = None
    return {
        "id": model_id,
        "name": name,
        "context_length": context,
        "prompt_price": str(price.get("prompt")) if price.get("prompt") is not None else None,
        "completion_price": str(price.get("completion")) if price.get("completion") is not None else None,
        "price_tier": price_tier,
        "input_modalities": inputs,
        "output_modalities": outputs,
        "supports_chat": supports_chat,
        "supports_embeddings": supports_embeddings,
    }


def _discover_openrouter_model_capabilities(
    chat_base: str,
    chat_key: str,
    embedding_base: str,
    embedding_key: str,
    include_embeddings: bool = True,
) -> dict:
    """Use OpenRouter's full metadata for chat options and probe embeddings.

    Chat catalogue entries are shown based on declared modalities instead of
    hiding hundreds of valid models behind a costly per-model inference call.
    Embeddings are still actively probed and only offered when their vector
    size matches the application's configured storage dimension.
    """
    raw_catalog = _fetch_openrouter_model_catalog(chat_base, chat_key)
    if not raw_catalog:
        raise LLMError("OpenRouter کاتالوگ خالی برگرداند؛ وضعیت حساب یا دسترسی مدل‌ها را بررسی کنید.")

    embedding_ids: List[str] = []
    if include_embeddings and _is_openrouter_host(embedding_base):
        embedding_ids = _fetch_openrouter_embedding_catalog(embedding_base, embedding_key)
        if not embedding_ids and embedding_base == chat_base:
            # The endpoint may be temporarily unavailable; do not fail the
            # complete chat catalogue just because embedding discovery failed.
            logger.warning("OpenRouter embedding catalogue was unavailable during model discovery")
    catalog_by_id = {}
    for item in raw_catalog:
        model_id = str(item.get("id") or "").strip()
        if model_id and model_id not in catalog_by_id:
            catalog_by_id[model_id] = item
    for model_id in embedding_ids:
        catalog_by_id.setdefault(model_id, {"id": model_id, "name": model_id})

    catalog = [
        _openrouter_catalog_entry(item, set(embedding_ids))
        for item in catalog_by_id.values()
    ]
    catalog.sort(key=lambda entry: (entry["name"].casefold(), entry["id"].casefold()))
    chat_models = sorted(
        {entry["id"] for entry in catalog if entry["supports_chat"]},
        key=str.casefold,
    )

    # For a separate non-OpenRouter embedding provider, look at its own
    # catalogue and try name/architecture hints as well; its API key is never
    # sent to the chat-provider endpoint.
    embedding_candidates = list(embedding_ids) if include_embeddings else []
    if include_embeddings and not _is_openrouter_host(embedding_base):
        try:
            emb_items = _list_models_raw(embedding_base, embedding_key)
        except Exception as exc:  # don't discard a valid chat catalogue for a separate embedding outage
            logger.warning("Could not read separate embedding catalogue (%s)", type(exc).__name__)
            emb_items = []
        emb_ids = [str(_field(item, "id", "") or "").strip() for item in emb_items]
        emb_ids = [model_id for model_id in emb_ids if model_id]
        emb_by_id = {str(_field(item, "id", "") or "").strip(): item for item in emb_items}
        declared, name_declared, _excluded, unknown = _classify_catalog(emb_ids, emb_by_id)
        embedding_candidates = _dedup_keep_order(
            declared, name_declared,
            [mid for mid in unknown if _looks_like_embedding_model(mid)],
        )
        cap = max(config.MAX_EMBEDDING_MODEL_PROBES, len(declared) + len(name_declared))
        embedding_candidates = embedding_candidates[:cap]

    from concurrent.futures import ThreadPoolExecutor

    verified_embeddings: List[str] = []
    def probe_embedding(model_id: str):
        try:
            emb_client = _client(embedding_base, embedding_key, short_timeout=True)
            ok, dimension = _probe_embedding_model(emb_client, model_id)
            return model_id, bool(ok and dimension == config.EMBEDDING_DIMENSIONS)
        except Exception:
            return model_id, False

    if embedding_candidates:
        with ThreadPoolExecutor(max_workers=min(config.MODEL_DISCOVERY_CONCURRENCY, len(embedding_candidates))) as pool:
            for model_id, ok in pool.map(probe_embedding, embedding_candidates):
                if ok:
                    verified_embeddings.append(model_id)
    verified_embeddings = sorted(set(verified_embeddings), key=str.casefold)
    verified_set = set(verified_embeddings)
    for entry in catalog:
        if entry["id"] in embedding_ids:
            # Discovery catalog membership is not proof of dimension fit.
            # This bit means the model is listed as an embedding offering;
            # verified models are separately returned as embedding_models.
            entry["supports_embeddings"] = True

    ids = sorted({entry["id"] for entry in catalog}, key=str.casefold)
    return {
        "models": ids,
        "chat_models": chat_models,
        "embedding_models": verified_embeddings,
        "unknown_models": sorted(
            [entry["id"] for entry in catalog if not entry["supports_chat"] and entry["id"] not in verified_set],
            key=str.casefold,
        ),
        "chat_probe_ok": bool(chat_models),
        "embedding_probe_ok": bool(verified_embeddings),
        "dual_capable_models": sorted(set(chat_models) & verified_set, key=str.casefold),
        "total_models_found": len(ids),
        "chat_candidates_probed": 0,
        "embedding_candidates_probed": len(embedding_candidates),
        "chat_candidates_truncated": False,
        "embedding_candidates_truncated": False,
        "model_catalog": catalog,
        "free_chat_models_count": sum(1 for entry in catalog if entry["supports_chat"] and entry["price_tier"] == "free"),
        "paid_chat_models_count": sum(1 for entry in catalog if entry["supports_chat"] and entry["price_tier"] == "paid"),
    }


def _fetch_openrouter_embedding_catalog(chat_base_url: str, api_key: str) -> List[str]:
    """Pull OpenRouter's dedicated embedding-model catalog.

    OpenRouter serves embedding-capable models from a separate
    `/embeddings/models` endpoint — they are intentionally left out of the
    general `/models` chat catalog that `list_models()` reads. Without this,
    no amount of name-matching on `/models` would ever surface them. This is
    best-effort: any failure (non-OpenRouter host, network error, unexpected
    shape) silently yields no extra candidates and the regular heuristic
    path still runs.
    """
    if not _is_openrouter_host(chat_base_url) or not api_key:
        return []
    try:
        parsed = urlparse(chat_base_url)
        path = parsed.path.rstrip("/") or "/api/v1"
        url = f"{parsed.scheme}://{parsed.netloc}{path}/embeddings/models"
        with httpx.Client(
            timeout=httpx.Timeout(
                config.MODEL_PROBE_TIMEOUT_SECONDS,
                connect=config.MODEL_PROBE_CONNECT_TIMEOUT_SECONDS,
            )
        ) as http_client:
            response = http_client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        if response.status_code != 200:
            return []
        payload = response.json()
        entries = payload.get("data") or []
        return [
            str(entry.get("id")).strip()
            for entry in entries
            if isinstance(entry, dict) and entry.get("id") and str(entry.get("id")).strip()
        ]
    except Exception:  # noqa: BLE001 — best-effort enrichment, never fatal
        return []


def _probe_embedding_model(client: OpenAI, model_id: str) -> tuple[bool, int | None]:
    """Return whether a model really serves embeddings and its output dimension."""
    response = client.embeddings.create(model=model_id, input="prismo-capability-probe")
    data = list(getattr(response, "data", []) or [])
    if not data or not getattr(data[0], "embedding", None):
        return False, None
    return True, len(data[0].embedding)


def _probe_chat_model(client: OpenAI, model_id: str) -> bool:
    """Verify that a model accepts a minimal chat-completion request."""
    response = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=1,
        temperature=0,
    )
    return bool(list(getattr(response, "choices", []) or []))


def _list_models_raw(base_url: str, api_key: str) -> List:
    """Fetch the raw /models catalog (SDK Model objects, not just ids)."""
    client = _client(base_url, api_key)
    try:
        response = client.models.list()
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, APIConnectionError):
            _log_connection_error(base_url, exc)
        raise LLMError(_friendly_error(exc)) from exc
    return list(getattr(response, "data", None) or [])


def _classify_catalog(models_list: List[str], by_id: dict) -> tuple:
    """Split a model-id list into (declared_chat, declared_embedding, excluded, unclassified)
    using provider-declared architecture metadata when available."""
    declared_chat, declared_embedding, excluded, unclassified = [], [], [], []
    for model_id in models_list:
        architecture = _architecture_info(by_id.get(model_id))
        verdict = _classify_by_architecture(architecture)
        if verdict == "embedding":
            declared_embedding.append(model_id)
        elif verdict == "chat":
            declared_chat.append(model_id)
        elif verdict == "excluded":
            excluded.append(model_id)
        else:
            unclassified.append(model_id)
    return declared_chat, declared_embedding, excluded, unclassified


def discover_model_capabilities(
    base_url: str,
    api_key: str,
    embedding_base_url: Optional[str] = None,
    embedding_api_key: Optional[str] = None,
    include_embeddings: bool = True,
) -> dict:
    """Discover chat models quickly, optionally probing embedding candidates too.

    Large gateways (OpenRouter and similar) can list hundreds of models, and
    OpenRouter publishes its embedding-capable models through a *separate*
    catalog endpoint entirely. To cover that without the discovery call
    taking forever or hammering the provider:
      1. Provider-declared architecture metadata (when present) classifies
         most candidates for free, with no probe needed to rule models out.
      2. Remaining candidates are probed for real (never trusted from
         metadata alone), bounded by MAX_CHAT_MODEL_PROBES /
         MAX_EMBEDDING_MODEL_PROBES so a very large catalog still returns
         promptly, with the most-likely candidates probed first.
      3. OpenRouter's dedicated embeddings catalog is queried in addition to
         `/models`, so embedding models that never appear there are not
         silently dropped.
    """
    chat_base = normalize_base_url(base_url)
    chat_key = (api_key or "").strip()
    if not chat_base or not chat_key:
        raise LLMError("Base URL و API Key سرویس چت را وارد کنید.")

    emb_base = normalize_base_url(embedding_base_url or chat_base)
    emb_key = (embedding_api_key or chat_key).strip()
    if _is_openrouter_host(chat_base):
        return _discover_openrouter_model_capabilities(chat_base, chat_key, emb_base, emb_key, include_embeddings)

    raw_items = _list_models_raw(chat_base, chat_key)
    models_list = sorted(
        {str(item.id).strip() for item in raw_items if getattr(item, "id", None) and str(item.id).strip()},
        key=str.casefold,
    )
    if not models_list:
        raise LLMError("سرویس متصل شد، اما هیچ مدلی در /models برنگرداند.")

    by_id = {}
    for item in raw_items:
        mid = str(getattr(item, "id", "") or "").strip()
        if mid and mid not in by_id:
            by_id[mid] = item

    chat_client = _client(chat_base, chat_key, short_timeout=True)

    declared_chat, declared_embedding, excluded, unclassified = _classify_catalog(models_list, by_id)
    excluded_set = set(excluded)

    name_hinted_embedding = [m for m in unclassified if _looks_like_embedding_model(m)]
    remaining = [m for m in unclassified if m not in name_hinted_embedding]
    likely_chat = [m for m in remaining if not _looks_non_text_output(m)]
    unlikely_chat = [m for m in remaining if _looks_non_text_output(m)]

    openrouter_embedding_ids = _fetch_openrouter_embedding_catalog(chat_base, emb_key) if include_embeddings else []

    chat_candidates_ordered = _dedup_keep_order(declared_chat, likely_chat, unlikely_chat)
    embedding_candidates_ordered = (
        _dedup_keep_order(openrouter_embedding_ids, declared_embedding, name_hinted_embedding)
        if include_embeddings else []
    )

    # The probe budget bounds the *uncertain* tail (name-guessed candidates on
    # providers that give no metadata at all) so a huge, metadata-free catalog
    # can't make discovery hang forever. It must never cut into candidates a
    # provider already confirmed (via architecture metadata or OpenRouter's own
    # embeddings catalog) -- those are cheap to verify and are exactly the
    # models this fix exists to stop silently dropping.
    chat_cap = max(config.MAX_CHAT_MODEL_PROBES, len(declared_chat))
    embedding_cap = max(config.MAX_EMBEDDING_MODEL_PROBES, len(declared_embedding) + len(openrouter_embedding_ids))

    total_chat_candidates = len(chat_candidates_ordered)
    total_embedding_candidates = len(embedding_candidates_ordered)
    chat_candidates = chat_candidates_ordered[:chat_cap]
    embedding_candidates = embedding_candidates_ordered[:embedding_cap]

    from concurrent.futures import ThreadPoolExecutor

    chat_verified: list[str] = []
    embedding_verified: list[str] = []

    def probe_chat(model_id: str):
        try:
            return model_id, _probe_chat_model(chat_client, model_id)
        except Exception:
            return model_id, False

    def probe_embedding(model_id: str):
        try:
            emb_client = _client(emb_base, emb_key, short_timeout=True)
            ok, dim = _probe_embedding_model(emb_client, model_id)
            return model_id, bool(ok and dim == config.EMBEDDING_DIMENSIONS), dim
        except Exception:
            return model_id, False, None

    task_count = max(len(chat_candidates) + len(embedding_candidates), 1)
    with ThreadPoolExecutor(max_workers=min(config.MODEL_DISCOVERY_CONCURRENCY, task_count)) as pool:
        futures = [("chat", pool.submit(probe_chat, model_id)) for model_id in chat_candidates]
        futures += [("embedding", pool.submit(probe_embedding, model_id)) for model_id in embedding_candidates]
        for kind, future in futures:
            if kind == "chat":
                model_id, ok = future.result()
                if ok:
                    chat_verified.append(model_id)
            else:
                model_id, ok, _dim = future.result()
                if ok:
                    embedding_verified.append(model_id)

    chat_verified = sorted(set(chat_verified), key=str.casefold)
    embedding_verified = sorted(set(embedding_verified), key=str.casefold)
    chat_set = set(chat_verified)
    embedding_set = set(embedding_verified)
    return {
        "models": models_list,
        "chat_models": chat_verified,
        "embedding_models": embedding_verified,
        "unknown_models": sorted(
            [m for m in models_list if m not in chat_set and m not in embedding_set and m not in excluded_set],
            key=str.casefold,
        ),
        "chat_probe_ok": bool(chat_verified),
        "embedding_probe_ok": bool(embedding_verified),
        "dual_capable_models": sorted(chat_set & embedding_set, key=str.casefold),
        "total_models_found": len(models_list),
        "chat_candidates_probed": len(chat_candidates),
        "embedding_candidates_probed": len(embedding_candidates),
        "chat_candidates_truncated": total_chat_candidates > len(chat_candidates),
        "embedding_candidates_truncated": total_embedding_candidates > len(embedding_candidates),
    }


def discover_embedding_models(base_url: str, api_key: str) -> dict:
    """Discover embedding models for a provider independently of any chat key.

    Powers the dedicated "discover embedding models" action for the separate
    embedding API key: it must work even when the chat key/base URL are
    empty or invalid, since the embedding provider can be entirely different
    from the chat provider.
    """
    emb_base = normalize_base_url(base_url)
    emb_key = (api_key or "").strip()
    if not emb_base or not emb_key:
        raise LLMError("Base URL و API Key سرویس embedding را وارد کنید.")

    raw_items = _list_models_raw(emb_base, emb_key)
    models_list = sorted(
        {str(item.id).strip() for item in raw_items if getattr(item, "id", None) and str(item.id).strip()},
        key=str.casefold,
    )
    if not models_list:
        raise LLMError("سرویس متصل شد، اما هیچ مدلی در /models برنگرداند.")

    by_id = {}
    for item in raw_items:
        mid = str(getattr(item, "id", "") or "").strip()
        if mid and mid not in by_id:
            by_id[mid] = item

    _declared_chat, declared_embedding, _excluded, unclassified = _classify_catalog(models_list, by_id)
    name_hinted = [m for m in unclassified if _looks_like_embedding_model(m)]
    other_unclassified = [m for m in unclassified if m not in name_hinted]

    openrouter_ids = _fetch_openrouter_embedding_catalog(emb_base, emb_key)
    candidates_ordered = _dedup_keep_order(openrouter_ids, declared_embedding, name_hinted, other_unclassified)

    embedding_cap = max(config.MAX_EMBEDDING_MODEL_PROBES, len(declared_embedding) + len(openrouter_ids))
    total_candidates = len(candidates_ordered)
    candidates = candidates_ordered[:embedding_cap]

    from concurrent.futures import ThreadPoolExecutor

    verified: list[str] = []

    def probe(model_id: str):
        try:
            client = _client(emb_base, emb_key, short_timeout=True)
            ok, dim = _probe_embedding_model(client, model_id)
            return model_id, bool(ok and dim == config.EMBEDDING_DIMENSIONS), dim
        except Exception:
            return model_id, False, None

    with ThreadPoolExecutor(max_workers=min(config.MODEL_DISCOVERY_CONCURRENCY, max(len(candidates), 1))) as pool:
        for model_id, ok, _dim in pool.map(probe, candidates):
            if ok:
                verified.append(model_id)

    verified = sorted(set(verified), key=str.casefold)
    return {
        "models": models_list,
        "embedding_models": verified,
        "embedding_probe_ok": bool(verified),
        "total_models_found": len(models_list),
        "embedding_candidates_probed": len(candidates),
        "embedding_candidates_truncated": total_candidates > len(candidates),
    }


def list_models(base_url: str, api_key: str) -> List[str]:
    """مدل‌های موجود در یک endpoint سازگار با OpenAI را بدون ذخیره‌ی کلید می‌خواند."""
    if not base_url:
        raise LLMError("آدرس سرویس (Base URL) را وارد کنید.")
    if not api_key:
        raise LLMError("API Key سرویس اختصاصی را وارد کنید.")

    raw_items = _list_models_raw(base_url, api_key)
    model_ids = sorted(
        {str(item.id).strip() for item in raw_items if getattr(item, "id", None) and str(item.id).strip()},
        key=str.casefold,
    )
    if not model_ids:
        raise LLMError("سرویس متصل شد، اما هیچ مدلی در /models برنگرداند.")
    return model_ids


def _error_chain(exc: Exception):
    """Yield the exception and its nested causes/contexts, avoiding cycles."""
    seen = set()
    current = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = getattr(current, "__cause__", None) or getattr(current, "__context__", None)


def _exception_text(exc: Exception) -> str:
    parts = []
    for item in _error_chain(exc):
        text = str(item).strip()
        if text:
            parts.append(text)
    return " | ".join(dict.fromkeys(parts))


def _classify_connection_error(exc: Exception) -> tuple[str, str]:
    """Return a stable diagnostic stage and a Persian explanation."""
    chain = list(_error_chain(exc))
    names = " ".join(type(item).__name__.lower() for item in chain)
    text = _exception_text(exc).lower()

    if "authenticationerror" in names or "401" in text:
        return "authentication", "احراز هویت سرویس رد شد؛ API Key یا مجوز دسترسی را بررسی کنید."
    if "sslerror" in names or "certificate" in text or "tls" in text:
        return "tls", "اتصال HTTPS برقرار شد اما گواهی TLS/SSL سرویس قابل تأیید نبود."
    if "gaierror" in names or "name or service not known" in text or "nodename nor servname" in text or "temporary failure in name resolution" in text or "failed to resolve" in text:
        return "dns", "نام دامنه سرویس از محیط Vercel قابل resolve نیست؛ DNS دامنه یا دسترسی خروجی Vercel را بررسی کنید."
    if "connecttimeout" in names or "connect timeout" in text:
        return "connect_timeout", "اتصال به سرور سرویس در مهلت تعیین‌شده برقرار نشد."
    if "readtimeout" in names or "read timeout" in text:
        return "read_timeout", "سرویس اتصال را پذیرفت اما در مهلت تعیین‌شده پاسخ نداد."
    if "connecterror" in names or "connection refused" in text or "connection reset" in text or "network is unreachable" in text:
        return "network", "Vercel نتوانست اتصال TCP به سرویس هوش مصنوعی برقرار کند."
    if "remoteprotocolerror" in names or "protocol error" in text:
        return "protocol", "پاسخ سرویس با پروتکل مورد انتظار OpenAI-compatible سازگار نبود."

    return "unknown", "سرویس خطای ارتباطی غیرقابل‌تشخیص برگرداند."


def _http_error_details(exc: Exception) -> tuple[Optional[int], str]:
    status = getattr(exc, "status_code", None)
    if status is not None:
        try:
            status = int(status)
        except (TypeError, ValueError):
            status = None

    body = ""
    response = getattr(exc, "response", None)
    if response is not None:
        try:
            body = response.text.strip()
        except Exception:  # noqa: BLE001
            body = ""
    if not body:
        message = getattr(exc, "message", None)
        if message:
            body = str(message).strip()
    return status, body[:1200]


def format_provider_error(
    exc: Exception,
    provider: ProviderConfig,
    operation: str = "درخواست مدل",
) -> str:
    """Build a user-visible diagnostic without ever exposing the API key."""
    status, body = _http_error_details(exc)
    if operation == "embedding":
        endpoint = normalize_base_url(provider.embedding_base_url or provider.base_url)
        model = provider.embedding_model
        configured_default_endpoint = normalize_base_url(
            config.AI_PROXY_BASE_URL or config.DEFAULT_PROVIDER_BASE_URL
        )
        configured_default_key = config.AI_PROXY_API_KEY or config.DEFAULT_PROVIDER_API_KEY
        provider_key = provider.embedding_api_key or provider.api_key
        is_default_endpoint = bool(
            endpoint and endpoint == configured_default_endpoint
            and provider_key == configured_default_key
        )
    else:
        endpoint = normalize_base_url(provider.base_url)
        model = provider.chat_model
        is_default_endpoint = bool(provider.is_default)

    if isinstance(exc, AuthenticationError) or status == 401:
        reason = "کلید API نامعتبر است یا سرویس دسترسی را رد کرده است."
        stage = "authentication"
    elif status == 403:
        reason = "سرویس درخواست Vercel را به‌دلیل مجوز یا محدودیت شبکه رد کرده است."
        stage = "authorization"
    elif status == 404:
        reason = "Endpoint یا مدل پیدا نشد؛ Base URL و نام مدل را بررسی کنید."
        stage = "http_404"
    elif status == 429:
        reason = "سرویس به‌دلیل محدودیت نرخ یا سهمیه درخواست را رد کرده است."
        stage = "rate_limit"
    elif status is not None and status >= 500:
        reason = f"خود سرویس هوش مصنوعی خطای HTTP {status} برگرداند."
        stage = f"http_{status}"
    elif isinstance(exc, APIConnectionError):
        stage, reason = _classify_connection_error(exc)
    elif isinstance(exc, APIError):
        stage = "api_error"
        reason = getattr(exc, "message", None) or str(exc) or "سرویس هوش مصنوعی خطا برگرداند."
    else:
        stage = "unexpected"
        reason = str(exc) or "خطای غیرمنتظره در ارتباط با سرویس هوش مصنوعی."

    details = [
        f"مرحله: {stage}",
        f"عملیات: {operation}",
        f"مدل: {model or 'نامشخص'}",
        f"Base URL: {endpoint or 'تنظیم نشده'}",
    ]
    if status is not None:
        details.append(f"HTTP: {status}")
    if body and body not in reason:
        details.append(f"جزئیات سرویس: {body}")

    # Include the nested exception only for diagnostics, never secrets.
    nested = _exception_text(exc)
    if nested and nested not in body:
        details.append(f"جزئیات فنی: {nested[:1200]}")

    if stage in {"connect_timeout", "network", "dns"} and is_default_endpoint and config.AI_PROXY_BASE_URL == "":
        details.append(
            "راه‌حل پیشنهادی: این سرویس از شبکه Vercel قابل دسترسی نیست؛ "
            "AI_PROXY_BASE_URL را روی یک Relay قابل‌دسترسی تنظیم کنید یا IP خروجی Vercel را در فایروال مقصد مجاز کنید."
        )

    return reason + "\n" + "\n".join(details)


def _friendly_error(exc: Exception) -> str:
    """Backward-compatible compact message for callers without provider context."""
    if isinstance(exc, AuthenticationError):
        return "کلید API نامعتبر است یا دسترسی رد شد. تنظیمات اتصال را بررسی کنید."
    if isinstance(exc, APIConnectionError):
        stage, reason = _classify_connection_error(exc)
        return f"{reason}\nمرحله: {stage}\nجزئیات فنی: {_exception_text(exc)[:1200]}"
    if isinstance(exc, APIError):
        return f"سرویس هوش مصنوعی خطا برگرداند: {getattr(exc, 'message', str(exc))}"
    return f"خطای غیرمنتظره در ارتباط با مدل: {exc}"


def _log_connection_error(base_url: str, exc: Exception) -> None:
    """Log enough detail to diagnose hosted egress/DNS issues without logging secrets."""
    stage, _ = _classify_connection_error(exc)
    logger.warning(
        "AI provider connection failed: base_url=%s stage=%s error_type=%s error=%s",
        normalize_base_url(base_url),
        stage,
        type(exc).__name__,
        _exception_text(exc)[:1500],
    )


def _provider_dns(base_url: str) -> list[str]:
    parsed = urlparse(normalize_base_url(base_url))
    if not parsed.hostname:
        return []
    addresses = set()
    try:
        for item in socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM):
            addresses.add(item[4][0])
    except Exception:
        return []
    return sorted(addresses)


def provider_diagnostics(provider: ProviderConfig) -> dict:
    """Run a lightweight connectivity diagnosis and return safe technical details."""
    started = time.perf_counter()
    endpoint = normalize_base_url(provider.base_url)
    result = {
        "ok": False,
        "base_url": endpoint,
        "model": provider.chat_model,
        "dns": _provider_dns(endpoint),
        "stage": "validation",
        "status_code": None,
        "error_type": None,
        "message": "",
        "elapsed_ms": 0,
    }

    def _success(message: str, stage: str, status_code: Optional[int] = 200) -> dict:
        result["ok"] = True
        result["stage"] = stage
        result["status_code"] = status_code
        result["message"] = message
        return result

    if not endpoint:
        result["message"] = "Base URL تنظیم نشده است."
        return result

    try:
        client = _client(endpoint, provider.api_key)
        try:
            response = client.models.list()
            model_ids = {
                str(item.id).strip()
                for item in response.data
                if getattr(item, "id", None) and str(item.id).strip()
            }
            if model_ids and provider.chat_model not in model_ids:
                # بعضی gatewayها /models را محدود یا alias می‌کنند؛ یک probe کوچک
                # روی مدل انتخاب‌شده انجام می‌دهیم تا false-negative نداشته باشیم.
                try:
                    client.chat.completions.create(
                        model=provider.chat_model,
                        messages=[{"role": "user", "content": "ping"}],
                        max_tokens=1,
                    )
                    return _success(
                        f"اتصال برقرار است؛ مدل «{provider.chat_model}» مستقیماً پاسخ داد، هرچند در /models فهرست نشده بود.",
                        "chat_probe",
                    )
                except Exception as probe_exc:  # noqa: BLE001
                    raise probe_exc
            return _success("DNS، اتصال HTTPS و endpoint /models با موفقیت پاسخ داد.", "models")
        except Exception as model_exc:  # noqa: BLE001
            status_code = getattr(model_exc, "status_code", None)
            if status_code in (404, 405, 501):
                try:
                    client.chat.completions.create(
                        model=provider.chat_model,
                        messages=[{"role": "user", "content": "ping"}],
                        max_tokens=1,
                    )
                    return _success(
                        "اتصال برقرار است؛ سرویس /models ندارد اما endpoint چت پاسخ داد.",
                        "chat_probe",
                    )
                except Exception as probe_exc:  # noqa: BLE001
                    model_exc = probe_exc
            raise model_exc
    except Exception as exc:  # noqa: BLE001
        result["status_code"], body = _http_error_details(exc)
        result["error_type"] = type(exc).__name__
        if isinstance(exc, APIConnectionError):
            result["stage"], result["message"] = _classify_connection_error(exc)
            _log_connection_error(endpoint, exc)
        else:
            result["stage"] = "http" if result["stage"] == "validation" else result["stage"]
            if isinstance(exc, APIError):
                result["message"] = format_provider_error(exc, provider, operation="connection test")
            else:
                result["message"] = body or _friendly_error(exc)
        result["message"] = f"{result['message']}\nجزئیات فنی: {_exception_text(exc)[:1200]}"
    finally:
        result["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
    return result


def _embedding_status_code(exc: Exception) -> Optional[int]:
    status, _ = _http_error_details(exc)
    return status


def _is_transient_embedding_error(exc: Exception) -> bool:
    status = _embedding_status_code(exc)
    return isinstance(exc, APIConnectionError) or status in {408, 425, 429, 500, 502, 503, 504}


def _is_embedding_batch_limit_error(exc: Exception) -> bool:
    status, body = _http_error_details(exc)
    if status == 413:
        return True
    if status not in {400, 422}:
        return False
    message = body.casefold()
    return any(
        hint in message
        for hint in (
            "too many inputs", "too many items", "batch size", "batch limit",
            "input is too long", "input length", "too many tokens",
            "maximum number of inputs", "payload too large", "request too large",
        )
    )


def _embedding_vectors_from_response(response, expected_count: int) -> List[List[float]]:
    data = list(_field(response, "data", []) or [])

    def response_index(item) -> int:
        try:
            return int(_field(item, "index", -1))
        except (TypeError, ValueError):
            return -1

    ordered = sorted(data, key=response_index)
    indices = [response_index(item) for item in ordered]
    if len(ordered) != expected_count or indices != list(range(expected_count)):
        raise LLMError("پاسخ سرویس embedding ناقص است یا ترتیب معتبر ندارد.")
    vectors = [_field(item, "embedding", None) for item in ordered]
    if any(not isinstance(vector, (list, tuple)) or not vector for vector in vectors):
        raise LLMError("سرویس embedding برای بخشی از ورودی‌ها بردار معتبری برنگرداند.")
    return [list(vector) for vector in vectors]


def _request_embedding_vectors(
    client: OpenAI,
    texts: List[str],
    provider: ProviderConfig,
    *,
    split_depth: int = 0,
) -> List[List[float]]:
    """Call an embedding provider reliably, retrying transient faults and splitting oversized batches."""
    response = None
    for attempt in range(3):
        try:
            response = client.embeddings.create(
                model=provider.embedding_model,
                input=texts,
            )
            break
        except Exception as exc:  # noqa: BLE001
            # Some OpenRouter/provider routes accept arrays but impose a smaller
            # batch ceiling. Split only when the provider identifies a payload/batch
            # limit; do not fan out ordinary invalid-model errors into many calls.
            if len(texts) > 1 and split_depth < 8 and _is_embedding_batch_limit_error(exc):
                midpoint = max(1, len(texts) // 2)
                return (
                    _request_embedding_vectors(client, texts[:midpoint], provider, split_depth=split_depth + 1)
                    + _request_embedding_vectors(client, texts[midpoint:], provider, split_depth=split_depth + 1)
                )

            if attempt < 2 and _is_transient_embedding_error(exc):
                # The normal path adds no delay; short backoff applies only after a
                # transient network/rate-limit/server failure.
                time.sleep(0.25 * (2 ** attempt))
                continue

            if isinstance(exc, APIConnectionError):
                _log_connection_error(provider.embedding_base_url or provider.base_url, exc)
            raise LLMError(format_provider_error(exc, provider, operation="embedding")) from exc

    if response is None:
        raise LLMError("سرویس embedding پس از چند تلاش پاسخ نداد.")
    return _embedding_vectors_from_response(response, len(texts))


def embed_texts(
    texts: List[str],
    provider: ProviderConfig,
) -> List[List[float]]:
    if not texts:
        return []

    client = _client(
        provider.embedding_base_url or provider.base_url,
        provider.embedding_api_key or provider.api_key,
    )
    embeddings = _request_embedding_vectors(client, texts, provider)

    expected_dimension = config.EMBEDDING_DIMENSIONS
    for embedding in embeddings:
        actual_dimension = len(embedding)
        if actual_dimension != expected_dimension:
            raise LLMError(
                "اندازه embedding با تنظیمات پروژه هماهنگ نیست. "
                f"Received={actual_dimension}, Expected={expected_dimension}. "
                "یک مدل embedding با بُعد سازگار انتخاب کنید."
            )
    return embeddings


def embed_text(text: str, provider: ProviderConfig) -> List[float]:
    return embed_texts([text], provider)[0]


def _visible_message_text(message) -> str:
    """Extract user-facing text from OpenAI-compatible message content.

    Some provider gateways return content as structured text parts instead of
    a plain string. Reasoning fields are intentionally not shown as answers.
    """
    content = _field(message, "content", None)
    if isinstance(content, str):
        text = content.strip()
        if text:
            return text
    elif isinstance(content, (list, tuple)):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                value = part.strip()
            else:
                value = _field(part, "text", None)
                value = value.strip() if isinstance(value, str) else ""
            if value:
                parts.append(value)
        if parts:
            return "\n".join(parts).strip()
    elif isinstance(content, dict):
        value = _field(content, "text", None)
        if isinstance(value, str) and value.strip():
            return value.strip()

    refusal = _field(message, "refusal", None)
    return refusal.strip() if isinstance(refusal, str) else ""


def chat_completion(
    messages: List[dict], provider: ProviderConfig, temperature: float = 0.7,
    model: Optional[str] = None, max_tokens: Optional[int] = None, fast_mode: bool = False,
) -> str:
    client = _client(provider.base_url, provider.api_key)
    selected_model = model or provider.chat_model
    empty_response_message = (
        "مدل پاسخ متنی برنگرداند. یک بار دیگر تلاش کنید؛ اگر تکرار شد، مدل دیگری را انتخاب یا اتصال API را بررسی کنید."
    )
    try:
        # Only retry an otherwise successful but empty model response once.
        for attempt in range(2):
            response = client.chat.completions.create(
                model=selected_model,
                messages=messages,
                temperature=temperature if attempt == 0 else min(float(temperature), 0.2),
                max_tokens=max_tokens or config.AI_MAX_OUTPUT_TOKENS,
                **_fast_reasoning_kwargs(provider, selected_model, fast_mode),
            )
            choices = _field(response, "choices", None) or []
            choice = choices[0] if choices else None
            message = _field(choice, "message", None) if choice is not None else None
            reply = _visible_message_text(message) if message is not None else ""
            if reply:
                return reply
            finish_reason = _field(choice, "finish_reason", "unknown") if choice is not None else "no_choices"
            logger.warning(
                "provider_empty_chat_response model=%s attempt=%s finish_reason=%s",
                selected_model, attempt + 1, finish_reason,
            )
    except LLMError:
        raise
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, APIConnectionError):
            _log_connection_error(provider.base_url, exc)
        raise LLMError(format_provider_error(exc, provider, operation="chat")) from exc
    raise LLMError(empty_response_message)


def stream_chat_completion(
    messages: List[dict], provider: ProviderConfig, temperature: float = 0.7,
    model: Optional[str] = None, max_tokens: Optional[int] = None, fast_mode: bool = False,
):
    """پاسخ مدل را تکه‌تکه (به‌صورت generator از رشته‌ها) برمی‌گرداند.

    خطاها همان LLMError فارسی و قابل‌نمایش‌اند؛ چه قبل از اولین تکه چه وسط پاسخ.
    """
    client = _client(provider.base_url, provider.api_key)
    selected_model = model or provider.chat_model
    try:
        stream = client.chat.completions.create(
            model=selected_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens or config.AI_MAX_OUTPUT_TOKENS,
            stream=True,
            **_fast_reasoning_kwargs(provider, selected_model, fast_mode),
        )
        for chunk in stream:
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            piece = getattr(delta, "content", None) if delta is not None else None
            if piece:
                yield piece
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, APIConnectionError):
            _log_connection_error(provider.base_url, exc)
        raise LLMError(format_provider_error(exc, provider, operation="chat")) from exc


def timed_chat_completion(
    messages: List[dict], provider: ProviderConfig, model: str, temperature: float = 0.7
) -> Tuple[str, int, Optional[str]]:
    """برای حالت Battle: پاسخ، زمان صرف‌شده (ms) و متن خطا (در صورت وجود) را برمی‌گرداند."""
    start = time.perf_counter()
    try:
        reply = chat_completion(messages, provider, temperature=temperature, model=model)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return reply, elapsed_ms, None
    except LLMError as exc:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return "", elapsed_ms, str(exc)


def test_connection(provider: ProviderConfig) -> Tuple[bool, str]:
    """Check provider reachability and the selected model without hiding the real error."""
    result = provider_diagnostics(provider)
    return bool(result["ok"]), str(result["message"])
