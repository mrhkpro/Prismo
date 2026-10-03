"""
لایه‌ی ارتباط با سرویس هوش مصنوعی (هر سرویس سازگار با OpenAI API).

اگر کاربر تنظیمات اختصاصی خودش (Base URL + API Key) را وارد نکرده باشد یا
صراحتاً «استفاده از مدل رایگان آماده» را فعال گذاشته باشد، از ارائه‌دهنده‌ی
پیش‌فرض تعریف‌شده در config استفاده می‌شود.
"""
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

from ..exceptions import LLMError

from openai import OpenAI, APIError, APIConnectionError, AuthenticationError

from .. import config, models


@dataclass
class ProviderConfig:
    base_url: str
    api_key: str
    chat_model: str
    embedding_model: str
    is_default: bool


def resolve_provider(settings: models.UserSettings) -> ProviderConfig:
    """بر اساس تنظیمات کاربر، مشخصات نهاییِ ارائه‌دهنده را برمی‌گرداند."""
    use_custom = (not settings.use_default_provider) and settings.api_key and settings.base_url
    if use_custom:
        return ProviderConfig(
            base_url=settings.base_url,
            api_key=settings.api_key,
            chat_model=settings.chat_model or config.DEFAULT_CHAT_MODEL,
            embedding_model=settings.embedding_model or config.DEFAULT_EMBEDDING_MODEL,
            is_default=False,
        )
    return ProviderConfig(
        base_url=config.DEFAULT_PROVIDER_BASE_URL,
        api_key=config.DEFAULT_PROVIDER_API_KEY,
        chat_model=settings.chat_model or config.DEFAULT_CHAT_MODEL,
        embedding_model=settings.embedding_model or config.DEFAULT_EMBEDDING_MODEL,
        is_default=True,
    )


def normalize_base_url(base_url: str) -> str:
    """URL ورودی سرویس سفارشی را برای SDK یکدست می‌کند، بدون تغییر مسیر endpoint."""
    return (base_url or "").strip().rstrip("/")


def _client(base_url: str, api_key: str) -> OpenAI:
    return OpenAI(base_url=normalize_base_url(base_url), api_key=api_key)


def list_models(base_url: str, api_key: str) -> List[str]:
    """مدل‌های موجود در یک endpoint سازگار با OpenAI را بدون ذخیره‌ی کلید می‌خواند."""
    if not base_url:
        raise LLMError("آدرس سرویس (Base URL) را وارد کنید.")
    if not api_key:
        raise LLMError("API Key سرویس اختصاصی را وارد کنید.")

    client = _client(base_url, api_key)
    try:
        response = client.models.list()
    except Exception as exc:  # noqa: BLE001
        raise LLMError(_friendly_error(exc)) from exc

    model_ids = sorted(
        {str(item.id).strip() for item in response.data if getattr(item, "id", None) and str(item.id).strip()},
        key=str.casefold,
    )
    if not model_ids:
        raise LLMError("سرویس متصل شد، اما هیچ مدلی در /models برنگرداند.")
    return model_ids


def _friendly_error(exc: Exception) -> str:
    if isinstance(exc, AuthenticationError):
        return "کلید API نامعتبر است یا دسترسی رد شد. تنظیمات اتصال را بررسی کنید."
    if isinstance(exc, APIConnectionError):
        return "اتصال به سرویس هوش مصنوعی برقرار نشد. آدرس سرویس (Base URL) و اتصال اینترنت را بررسی کنید."
    if isinstance(exc, APIError):
        return f"سرویس هوش مصنوعی خطا برگرداند: {getattr(exc, 'message', str(exc))}"
    return f"خطای غیرمنتظره در ارتباط با مدل: {exc}"


def embed_texts(
    texts: List[str],
    provider: ProviderConfig,
) -> List[List[float]]:

    if not texts:
        return []

    client = _client(
        provider.base_url,
        provider.api_key,
    )

    try:

        response = client.embeddings.create(
            model=provider.embedding_model,
            input=texts,
        )

    except Exception as exc:  # noqa: BLE001

        raise LLMError(
            _friendly_error(exc)
        ) from exc

    # --------------------------------------------------------
    # Preserve input ordering
    # --------------------------------------------------------

    ordered = sorted(
        response.data,
        key=lambda item: item.index,
    )

    if (
        len(ordered) != len(texts)
        or [item.index for item in ordered] != list(range(len(texts)))
    ):
        raise LLMError(
            "پاسخ سرویس embedding ناقص است یا ترتیب معتبر ندارد."
        )

    embeddings = [
        item.embedding
        for item in ordered
    ]

    # --------------------------------------------------------
    # Validate embedding dimensions
    # --------------------------------------------------------

    expected_dimension = (
        config.EMBEDDING_DIMENSIONS
    )

    for embedding in embeddings:

        actual_dimension = len(
            embedding
        )

        if actual_dimension != expected_dimension:

            raise LLMError(
                "اندازه embedding با تنظیمات پروژه "
                "هماهنگ نیست. "
                f"Received={actual_dimension}, "
                f"Expected={expected_dimension}."
            )

    return embeddings


def embed_text(text: str, provider: ProviderConfig) -> List[float]:
    return embed_texts([text], provider)[0]


def chat_completion(
    messages: List[dict], provider: ProviderConfig, temperature: float = 0.7, model: Optional[str] = None
) -> str:
    client = _client(provider.base_url, provider.api_key)
    try:
        response = client.chat.completions.create(
            model=model or provider.chat_model,
            messages=messages,
            temperature=temperature,
        )
    except Exception as exc:  # noqa: BLE001
        raise LLMError(_friendly_error(exc)) from exc
    return response.choices[0].message.content or ""


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
    """یک تماس سبک برای بررسی صحت تنظیمات اتصال (Settings > Test Connection)."""
    client = _client(provider.base_url, provider.api_key)
    try:
        client.chat.completions.create(
            model=provider.chat_model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=4,
        )
        return True, "اتصال با موفقیت برقرار شد."
    except Exception as exc:  # noqa: BLE001
        return False, _friendly_error(exc)
