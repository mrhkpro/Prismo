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

logger = logging.getLogger("quasar.llm")


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


def _client(base_url: str, api_key: str) -> OpenAI:
    """Create/reuse an OpenAI-compatible client with serverless-friendly timeouts."""
    normalized = normalize_base_url(base_url)
    if not normalized:
        raise LLMError("آدرس سرویس (Base URL) را وارد کنید.")
    if not api_key:
        raise LLMError("API Key سرویس را وارد کنید.")
    return _cached_client(normalized, api_key)


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
        if isinstance(exc, APIConnectionError):
            _log_connection_error(base_url, exc)
        raise LLMError(_friendly_error(exc)) from exc

    model_ids = sorted(
        {str(item.id).strip() for item in response.data if getattr(item, "id", None) and str(item.id).strip()},
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
    endpoint = normalize_base_url(provider.base_url)
    model = provider.chat_model if operation != "embedding" else provider.embedding_model

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
        if isinstance(exc, APIConnectionError):
            _log_connection_error(provider.base_url, exc)
        raise LLMError(format_provider_error(exc, provider, operation="embedding")) from exc

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
        selected_model = model or provider.chat_model
        response = client.chat.completions.create(
            model=selected_model,
            messages=messages,
            temperature=temperature,
            max_tokens=config.AI_MAX_OUTPUT_TOKENS,
        )
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, APIConnectionError):
            _log_connection_error(provider.base_url, exc)
        raise LLMError(format_provider_error(exc, provider, operation="chat")) from exc
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
    """Check provider reachability and the selected model without hiding the real error."""
    result = provider_diagnostics(provider)
    return bool(result["ok"]), str(result["message"])
