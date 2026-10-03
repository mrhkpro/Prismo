class AppError(Exception):
    """خطای قابل‌نمایش برای API که پیام آن عمداً برای کاربر مناسب شده است."""

    status_code = 500


class LLMError(AppError):
    """خطای ارتباط/پاسخ سرویس هوش مصنوعی."""

    status_code = 502
