"""پاسخ‌های فوری برای پیام‌های روزمره و پرتکرار.

این مسیر عمداً قبل از embedding و تماس با مدل اجرا می‌شود تا احوال‌پرسی،
تشکر و سؤال‌های عمومی چندین برابر سریع‌تر پاسخ داده شوند.
"""

from __future__ import annotations

import re
from typing import Optional


_RESPONSES = (
    (
        re.compile(r"^(?:سلام|سلاممم+|درود|hi|hello|hey)(?:\s*[!؟?،.]*)$", re.I),
        "سلام! 👋 خوشحالم می‌بینمت. چه کمکی از دستم برمیاد؟",
    ),
    (
        re.compile(r"^(?:خوبی|خوبی؟|حالت چطوره|حالت خوبه|چطوری|چه خبر)(?:\s*[!؟?،.]*)$", re.I),
        "مرسی که پرسیدی 😊 خوبم و آماده‌ام کمکت کنم. تو چطوری؟",
    ),
    (
        re.compile(r"^(?:ممنون|مرسی|متشکرم|خیلی ممنون|دمت گرم)(?:\s*[!؟?،.]*)$", re.I),
        "خواهش می‌کنم 🌱",
    ),
    (
        re.compile(r"^(?:خداحافظ|فعلا|فعلاً|بای|bye)(?:\s*[!؟?،.]*)$", re.I),
        "خداحافظ! 👋 هر وقت خواستی من اینجام.",
    ),
    (
        re.compile(r"^(?:تو کی هستی|اسمت چیه|چه کاره‌ای|چی هستی)(?:\s*[!؟?،.]*)$", re.I),
        "من دستیار هوشمند همین ویجتم؛ برای پاسخ‌دادن به سؤال‌ها و کمک‌کردن بهت اینجام.",
    ),
    (
        re.compile(r"^(?:چی کار می‌کنی|چه کمکی می‌تونی بکنی|چه کارهایی بلدی|چیکار می‌تونی بکنی)(?:\s*[!؟?،.]*)$", re.I),
        "می‌تونم بر اساس دانشنامه‌ات به سؤال‌ها جواب بدم و درباره اطلاعات موجود در اسناد راهنماییت کنم.",
    ),
)


def _normalize(text: str) -> str:
    text = (text or "").strip().lower()
    text = text.replace("ي", "ی").replace("ى", "ی").replace("ك", "ک")
    text = text.replace("ۀ", "ه").replace("ة", "ه")
    # ایموجی و نشانه‌های تزئینی نباید باعث شوند «سلام 👋» از پاسخ آماده خارج شود.
    text = re.sub(r"[\U0001F1E6-\U0001FAFF\u2600-\u27BF]", " ", text)
    text = re.sub(r"[\u200d\ufe0f]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


_RESPONSES_EN = (
    (re.compile(r"^(?:سلام|سلاممم+|درود|hi|hello|hey)(?:\s*[!؟?،.]*)$", re.I), "Hello! 👋 Nice to see you. How can I help?"),
    (re.compile(r"^(?:خوبی|خوبی؟|حالت چطوره|حالت خوبه|چطوری|چه خبر)(?:\s*[!؟?،.]*)$", re.I), "Thanks for asking 😊 I’m doing well and ready to help. How are you?"),
    (re.compile(r"^(?:ممنون|مرسی|متشکرم|خیلی ممنون|دمت گرم)(?:\s*[!؟?،.]*)$", re.I), "You’re welcome 🌱"),
    (re.compile(r"^(?:خداحافظ|فعلا|فعلاً|بای|bye)(?:\s*[!؟?،.]*)$", re.I), "Goodbye! 👋 I’ll be here whenever you need me."),
    (re.compile(r"^(?:تو کی هستی|اسمت چیه|چه کاره‌ای|چی هستی)(?:\s*[!؟?،.]*)$", re.I), "I’m the smart assistant for this widget. I’m here to answer questions and help you."),
    (re.compile(r"^(?:چی کار می‌کنی|چه کمکی می‌تونی بکنی|چه کارهایی بلدی|چیکار می‌تونی بکنی)(?:\s*[!؟?،.]*)$", re.I), "I can answer questions from your knowledge base and guide you through the information in your documents."),
)


def get_common_response(text: str, language: str = "fa") -> Optional[str]:
    """Return a fast canned response; long messages skip this path."""
    normalized = _normalize(text)
    if not normalized or len(normalized) > 64:
        return None
    response_set = _RESPONSES_EN if language == "en" else _RESPONSES
    for pattern, reply in response_set:
        if pattern.fullmatch(normalized):
            return reply
    return None
