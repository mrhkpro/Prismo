from types import SimpleNamespace
from unittest.mock import patch

from app.routers import public_widget
from app.services.response_quality import looks_like_mixed_script_noise


def test_mixed_script_token_soup_is_flagged_but_persian_english_is_not():
    noise = (
        ("فارسی " * 18)
        + ("calculation deployment model " * 14)
        + ("中文字符 " * 12)
        + ("русский текст " * 10)
        + ("한국어 문장 " * 8)
        + ("ภาษาไทย " * 8)
    )
    good = "برای محاسبهٔ هزینه، ابتدا تعداد واحدها را در قیمت هر واحد ضرب کنید. For example, total = quantity × unit price."

    assert looks_like_mixed_script_noise(noise)
    assert not looks_like_mixed_script_noise(good)
    assert not looks_like_mixed_script_noise("سلام! چطور می‌توانم کمک کنم؟")


def _plan():
    return SimpleNamespace(
        messages=[{"role": "user", "content": "پاسخ بده"}],
        provider=object(),
        temperature=0.8,
        model="test-chat-model",
        cache_allowed=True,
    )


def test_widget_quality_guard_retries_before_emitting_corrupted_text():
    noise = (
        ("فارسی " * 18)
        + ("calculation deployment model " * 14)
        + ("中文字符 " * 12)
        + ("русский текст " * 10)
        + ("한국어 문장 " * 8)
        + ("ภาษาไทย " * 8)
    )
    corrected = "این پاسخ اصلاح‌شده و قابل‌خواندن است و اطلاعات را به فارسی توضیح می‌دهد."
    plan = _plan()
    collected = []

    with patch.object(public_widget.llm_client, "stream_chat_completion", return_value=iter([noise[:70], noise[70:150], noise[150:]])), \
         patch.object(public_widget.llm_client, "chat_completion", return_value=corrected) as retry:
        frames = list(public_widget._stream_checked_model_reply(plan, collected, "fa"))

    rendered_text = "".join(collected)
    assert corrected == rendered_text
    assert "calculation deployment model" not in rendered_text
    assert "中文字符" not in rendered_text
    assert retry.call_args.kwargs["temperature"] <= 0.2
    assert plan.cache_allowed is True


def test_widget_quality_guard_falls_back_instead_of_showing_noise_when_retry_is_bad():
    noise = (
        ("فارسی " * 18)
        + ("calculation deployment model " * 14)
        + ("中文字符 " * 12)
        + ("русский текст " * 10)
        + ("한국어 문장 " * 8)
        + ("ภาษาไทย " * 8)
    )
    plan = _plan()
    collected = []

    with patch.object(public_widget.llm_client, "stream_chat_completion", return_value=iter([noise[:80], noise[80:160], noise[160:]])), \
         patch.object(public_widget.llm_client, "chat_completion", return_value=noise):
        frames = list(public_widget._stream_checked_model_reply(plan, collected, "fa"))

    rendered = "".join(frames)
    assert "متن قابل‌خواندنی تولید نکرد" in rendered
    assert "中文字符" not in rendered
    assert plan.cache_allowed is False


def test_admin_is_dark_only_and_accounts_do_not_show_admin_link():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    admin = (root / "frontend/admin.html").read_text(encoding="utf-8")
    dashboard = (root / "frontend/dashboard.html").read_text(encoding="utf-8")
    theme_js = (root / "frontend/assets/js/theme.js").read_text(encoding="utf-8")

    assert 'data-admin-dark-only="1"' in admin
    assert 'id="themeToggle"' not in admin
    assert 'document.documentElement.dataset.theme = "dark"' in admin
    assert 'id="openAdminLink"' not in dashboard
    assert 'href="/admin.html" id="openAdminLink"' not in dashboard
    assert "isAdminDarkOnly() ? \"dark\"" in theme_js
