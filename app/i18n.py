from __future__ import annotations

from fastapi import Request

from . import config

COMMON_MESSAGES_EN = {
    "دسترسی به پایگاه‌داده برقرار نشد.": "Database access could not be established.",
    "پایگاه‌داده موقتاً در دسترس نیست.": "The database service is temporarily unavailable.",
    "خطای اتصال به پایگاه‌داده.": "Database connection error.",
    "سرویس موقتاً در دسترس نیست.": "The service is temporarily unavailable.",
    "سرویس موقتاً در دسترس نیست": "The service is temporarily unavailable.",
    "ارتباط با سرویس قطع شد.": "The connection to the service was interrupted.",
    "ارتباط با سرور برقرار نشد.": "Could not connect to the server.",
    "ارتباط با سرور برقرار نشد. مطمئن شوید بک‌اند در حال اجراست.": "Could not connect to the server. Make sure the backend is running.",
    "نشست شما منقضی شده؛ دوباره وارد شوید.": "Your session has expired. Please sign in again.",
    "توکن نامعتبر است.": "Invalid token.",
    "کاربر یافت نشد.": "User not found.",
    "این بخش فقط برای مدیر سیستم در دسترس است.": "This section is available only to system administrators.",
    "این نام کاربری قبلاً ثبت شده است.": "This username is already registered.",
    "نام کاربری یا رمز عبور اشتباه است.": "Incorrect username or password.",
    "حساب کاربری شما مسدود شده است.": "Your account is blocked.",
    "ویجت یافت نشد.": "Widget not found.",
    "این سرویس در حال حاضر موقتاً در دسترس نیست.": "This service is temporarily unavailable.",
    "این سرویس موقتاً در دسترس نیست.": "This service is temporarily unavailable.",
    "تعداد درخواست‌ها زیاد است. چند لحظه بعد دوباره تلاش کنید.": "Too many requests. Please try again in a moment.",
    "نشست گفت‌وگو یافت نشد.": "Chat session not found.",
}


def get_language(request: Request | None) -> str:
    if request is None:
        return "fa"
    value = (request.headers.get("X-QZ-Language") or request.query_params.get("lang") or "fa").strip().lower()
    return "en" if value.startswith("en") else "fa"


def localize_message(message: str | None, language: str) -> str | None:
    if not message or language != "en":
        return message
    if message in COMMON_MESSAGES_EN:
        return COMMON_MESSAGES_EN[message]
    out = message
    for fa, en in sorted(COMMON_MESSAGES_EN.items(), key=lambda x: len(x[0]), reverse=True):
        out = out.replace(fa, en)
    return out


def localize_default_system_prompt(value: str | None, language: str) -> str:
    value = value or config.DEFAULT_SYSTEM_PROMPT
    if language == "en" and value in {config.DEFAULT_SYSTEM_PROMPT, config.DEFAULT_SYSTEM_PROMPT_EN}:
        return config.DEFAULT_SYSTEM_PROMPT_EN
    if language != "en" and value in {config.DEFAULT_SYSTEM_PROMPT, config.DEFAULT_SYSTEM_PROMPT_EN}:
        return config.DEFAULT_SYSTEM_PROMPT
    return value


def localize_widget_title(value: str | None, language: str) -> str:
    value = value or config.DEFAULT_WIDGET_TITLE
    if value in {config.DEFAULT_WIDGET_TITLE, config.DEFAULT_WIDGET_TITLE_EN}:
        return config.DEFAULT_WIDGET_TITLE_EN if language == "en" else config.DEFAULT_WIDGET_TITLE
    return value


def localize_widget_welcome(value: str | None, language: str) -> str:
    value = value or config.DEFAULT_WIDGET_WELCOME
    if value in {config.DEFAULT_WIDGET_WELCOME, config.DEFAULT_WIDGET_WELCOME_EN}:
        return config.DEFAULT_WIDGET_WELCOME_EN if language == "en" else config.DEFAULT_WIDGET_WELCOME
    return value
