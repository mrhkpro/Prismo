"""
جایگزین امن datetime.utcnow() که در نسخه‌های جدید پایتون منسوخ شده است.

خروجی این تابع عمداً یک datetime بدون timezone (naive) است -- دقیقاً همان
شکلی که datetime.utcnow() قبلاً برمی‌گرداند -- چون همه‌ی ستون‌های DateTime
در models.py بدون timezone=True تعریف شده‌اند و کد موجود (مقایسه‌ی تاریخ
انقضا، last_login_at و...) روی همین نوع مقدار حساب باز کرده. فقط فراخوانی
منسوخ جایگزین شده، رفتار دقیقاً همان است.
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
