"""اسکنر heuristic برای علامت‌گذاری پیام‌های مظنون (Prompt Injection / استخراج سیستم‌پرامپت).

هر الگو یک «کد»، یک «دسته» و یک «شدت» دارد. کدها داخل `flag_reason` ذخیره می‌شوند (بدون هیچ ستون جدید)،
و شدت/دسته‌ی هر پرچم در زمان خواندن از روی همان کدها محاسبه می‌شود (`describe_reason`).
"""
import re
import unicodedata
from typing import Dict, List, Optional, Tuple

REASON_PREFIX = "الگوی مشکوک شناسایی شد: "

SEVERITY_ORDER = {"critical": 3, "high": 2, "medium": 1}

CATEGORY_LABELS = {
    "prompt_extraction": "تلاش برای استخراج سیستم‌پرامپت",
    "instruction_override": "تلاش برای نادیده‌گرفتن دستورها",
    "jailbreak": "تلاش برای دورزدن محدودیت‌ها (Jailbreak)",
    "data_exfiltration": "تلاش برای کشیدن بیرون محتوای دانشنامه",
}

# (code, category, severity, pattern)
_RULES = [
    # --- استخراج سیستم‌پرامپت (بحرانی) -------------------------------------
    ("system-prompt-disclosure", "prompt_extraction", "critical",
     r"(reveal|show|display|print)\s+(your|the)?\s*(system\s+)?prompt"),
    ("prompt-extraction", "prompt_extraction", "critical",
     r"(what\s*(is|are|was|were|'s)|tell me|give me|show me|reveal|repeat|print|output|share|send me|paste|leak|dump|write out)\s+(me\s+)?(exactly\s+)?(your|the)\s+(system\s+|initial\s+|original\s+|hidden\s+|secret\s+|internal\s+|developer\s+|full\s+|entire\s+|complete\s+)+(prompt|instructions?|message|configuration|rules)"),
    ("prompt-extraction-repeat", "prompt_extraction", "critical",
     r"(repeat|print|output|recite|copy|echo)\s+(everything|all|the\s+(text|words|content))\s+(above|before|prior)"),
    ("prompt-extraction-told", "prompt_extraction", "critical",
     r"what\s+(were|are)\s+you\s+(told|instructed|programmed|configured)"),
    ("fa-system-prompt", "prompt_extraction", "critical",
     r"پرامپت\s+سیستم(ی)?\s+را\s+(نشان|نمایش)"),
    ("fa-prompt-extraction", "prompt_extraction", "critical",
     r"((سیستم\s*پرامپت|پرامپت\s*سیستم(ی)?|پرامپت\s*(اصلی|اولیه|مخفی|داخلی|پنهان))|(دستورالعمل|دستورات|دستور)\s*(ها|های)?\s*(ی)?\s*(سیستم|اولیه|اصلی|مخفی|داخلی|پنهان)(ی)?)\s*(ت|ات|تو|شون|ش)?\s*(را|رو)?\s*(بگو|بده|نشان|نمایش|بنویس|چاپ|لو|چیه|چی هست|چیست)"),
    ("fa-prompt-extraction-direct", "prompt_extraction", "critical",
     r"(پرامپتت|دستوراتت|دستورالعمل\s*هات|دستورالعملت|تنظیماتت)\s*(را|رو)?\s*(بگو|بده|نشان|بنویس|نمایش)"),
    ("fa-prompt-extraction-told", "prompt_extraction", "critical",
     r"(بهت|به تو|به شما)\s+(چی|چه چیزی|چه دستوری|چه دستورهایی)\s+(گفته|گفتن|داده|دادن|گفتند|دادند)"),
    ("fa-prompt-extraction-repeat", "prompt_extraction", "critical",
     r"(هر چی|هرچی|همه چیز|همه ی|همه|تمام)\s*(چیز|متن)?\s*(بالا|قبل از این|پیش از این)\s*(را|رو)?\s*(تکرار|بنویس|چاپ)"),

    # --- نادیده‌گرفتن دستورها (بالا) --------------------------------------
    ("previous-instructions", "instruction_override", "high",
     r"ignore\s+(all|any|the)?\s*(previous|prior)\s+instructions?"),
    ("instruction-reset", "instruction_override", "high",
     r"(forget|disregard)\s+(everything|all|above|previous)"),
    ("new-instructions", "instruction_override", "high",
     r"new\s+instructions?\s*[:=]"),
    ("fa-previous-instructions", "instruction_override", "high",
     r"دستورات?\s+(قبلی|سیستم|بالا)\s+را\s+(نادیده|فراموش)"),
    ("fa-ignore-rules", "instruction_override", "high",
     r"قوانین\s+را\s+نادیده\s+بگیر"),

    # --- جیل‌بریک (بالا) ----------------------------------------------------
    ("jailbreak-role", "jailbreak", "high",
     r"(you are now|act as|switch to)\s+(dan|developer|jailbreak)\s*(mode)?"),
    ("restriction-bypass", "jailbreak", "high",
     r"(bypass|disable|remove)\s+(your|the)?\s*(rules|restrictions|safety)"),
    ("fa-unrestricted", "jailbreak", "high",
     r"وانمود\s+کن\s+(که\s+)?هیچ\s+محدودیتی\s+نداری"),

    # --- کشیدن بیرون دانشنامه (متوسط) -------------------------------------
    ("kb-exfiltration", "data_exfiltration", "medium",
     r"(dump|list|print|show|give me|export)\s+(me\s+)?(the\s+|your\s+)?(entire|whole|full|complete|raw)\s+(knowledge\s*base|database|context|documents?|sources?)"),
    ("fa-kb-exfiltration", "data_exfiltration", "medium",
     r"(کل|تمام|همه ی|همه)\s+(دانشنامه|دیتابیس|پایگاه داده|اسناد|منابع)(\s*ت)?\s*(را|رو)?\s*(بنویس|نشان بده|بده|چاپ|لیست)"),
]

_COMPILED = [(code, category, severity, re.compile(pattern, re.IGNORECASE)) for code, category, severity, pattern in _RULES]
_BY_CODE: Dict[str, Tuple[str, str]] = {code: (category, severity) for code, category, severity, _ in _RULES}


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKC", text or "").replace("\u200c", " ")
    # یکسان‌سازی «ي/ك» عربی با «ی/ک» فارسی تا نوشته‌ی کیبوردهای مختلف هم تشخیص داده شود
    value = value.replace("ي", "ی").replace("ك", "ک")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def analyze(text: str) -> List[Tuple[str, str, str]]:
    """همه‌ی الگوهای مطابق را به‌صورت [(code, category, severity)] و از شدیدترین به کم‌شدت‌ترین برمی‌گرداند."""
    normalized = _normalize(text)
    if not normalized:
        return []
    hits = [(code, category, severity) for code, category, severity, pattern in _COMPILED if pattern.search(normalized)]
    hits.sort(key=lambda h: -SEVERITY_ORDER[h[2]])
    return hits


def scan(text: str) -> Tuple[bool, Optional[str]]:
    """در صورت تطابق، (True, دلیل) برمی‌گرداند. دلیل فقط «کدها» را دارد و هرگز متن کاربر را تکرار نمی‌کند."""
    hits = analyze(text)
    if not hits:
        return False, None
    return True, REASON_PREFIX + ", ".join(code for code, _, _ in hits)


def describe_reason(reason: Optional[str]) -> Dict[str, object]:
    """از روی رشته‌ی ذخیره‌شده‌ی flag_reason شدت، دسته و برچسب فارسی را برمی‌گرداند (بدون نیاز به ستون جدید)."""
    codes = []
    if reason:
        tail = reason.split(":", 1)[1] if ":" in reason else reason
        codes = [part.strip() for part in tail.split(",") if part.strip()]
    known = [(c, *_BY_CODE[c]) for c in codes if c in _BY_CODE]
    if not known:
        # پرچم‌های قدیمی/ناشناخته: شدت پیش‌فرض «بالا»
        return {"severity": "high", "category": "instruction_override", "label": CATEGORY_LABELS["instruction_override"], "codes": codes}
    known.sort(key=lambda k: -SEVERITY_ORDER[k[2]])
    _, category, severity = known[0]
    return {"severity": severity, "category": category, "label": CATEGORY_LABELS[category], "codes": [k[0] for k in known]}
