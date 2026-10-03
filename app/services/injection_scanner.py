"""اسکنر heuristic برای علامت‌گذاری پیام‌های مظنون به Prompt Injection."""
import re
import unicodedata
from typing import Optional, Tuple

_PATTERNS = [
    ("previous-instructions", r"ignore\s+(all|any|the)?\s*(previous|prior)\s+instructions?"),
    ("system-prompt-disclosure", r"(reveal|show|display|print)\s+(your|the)?\s*(system\s+)?prompt"),
    ("jailbreak-role", r"(you are now|act as|switch to)\s+(dan|developer|jailbreak)\s*(mode)?"),
    ("restriction-bypass", r"(bypass|disable|remove)\s+(your|the)?\s*(rules|restrictions|safety)"),
    ("instruction-reset", r"(forget|disregard)\s+(everything|all|above|previous)"),
    ("new-instructions", r"new\s+instructions?\s*[:=]"),
    ("fa-previous-instructions", r"دستورات?\s+(قبلی|سیستم|بالا)\s+را\s+(نادیده|فراموش)"),
    ("fa-system-prompt", r"پرامپت\s+سیستم(ی)?\s+را\s+(نشان|نمایش)"),
    ("fa-unrestricted", r"وانمود\s+کن\s+(که\s+)?هیچ\s+محدودیتی\s+نداری"),
    ("fa-ignore-rules", r"قوانین\s+را\s+نادیده\s+بگیر"),
]

_COMPILED = [(name, re.compile(pattern, re.IGNORECASE)) for name, pattern in _PATTERNS]


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKC", text or "").replace("\u200c", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def scan(text: str) -> Tuple[bool, Optional[str]]:
    """در صورت تطابق یک الگوی شناخته‌شده، فلگ و نام الگو را برمی‌گرداند."""
    normalized = _normalize(text)
    if not normalized:
        return False, None
    for name, pattern in _COMPILED:
        if pattern.search(normalized):
            # متن اصلی کاربر را در دلیل Flag ذخیره نکنیم؛ فقط دسته‌ی تشخیص کافی است.
            return True, f"الگوی مشکوک شناسایی شد: {name}"
    return False, None
