"""Small safety net for obviously corrupted, mixed-script model responses.

This is deliberately conservative: normal Persian/English answers may contain
one or two scripts, while a response mixing four or more unrelated scripts in
large quantities is almost always a broken generation rather than useful prose.
"""
from __future__ import annotations

import unicodedata
from collections import Counter

_SCRIPT_MARKERS = (
    ("Latin", "LATIN"),
    ("Arabic", "ARABIC"),
    ("Cyrillic", "CYRILLIC"),
    ("Han", "CJK UNIFIED IDEOGRAPH"),
    ("Han", "CJK COMPATIBILITY IDEOGRAPH"),
    ("Han", "IDEOGRAPHIC"),
    ("Hiragana", "HIRAGANA"),
    ("Katakana", "KATAKANA"),
    ("Hangul", "HANGUL"),
    ("Thai", "THAI"),
    ("Hebrew", "HEBREW"),
    ("Greek", "GREEK"),
    ("Devanagari", "DEVANAGARI"),
    ("Bengali", "BENGALI"),
    ("Armenian", "ARMENIAN"),
    ("Georgian", "GEORGIAN"),
    ("Tamil", "TAMIL"),
    ("Telugu", "TELUGU"),
    ("Malayalam", "MALAYALAM"),
    ("Kannada", "KANNADA"),
    ("Gujarati", "GUJARATI"),
    ("Gurmukhi", "GURMUKHI"),
    ("Lao", "LAO"),
    ("Myanmar", "MYANMAR"),
    ("Khmer", "KHMER"),
    ("Ethiopic", "ETHIOPIC"),
    ("Sinhala", "SINHALA"),
)


def _script_for(character: str) -> str | None:
    name = unicodedata.name(character, "")
    for label, marker in _SCRIPT_MARKERS:
        if marker in name:
            return label
    return None


def looks_like_mixed_script_noise(text: str, *, min_letters: int = 80, min_scripts: int = 4) -> bool:
    """Return true only for long output dominated by many unrelated writing systems."""
    if not text:
        return False

    counts: Counter[str] = Counter()
    total = 0
    for character in text:
        if not character.isalpha():
            continue
        total += 1
        script = _script_for(character)
        if script:
            counts[script] += 1

    if total < min_letters:
        return False
    substantial = {script: count for script, count in counts.items() if count >= 3}
    if len(substantial) < min_scripts:
        return False

    counted = sum(substantial.values())
    dominant_share = max(substantial.values()) / counted
    # A coherent bilingual response can mix scripts, but should still have a
    # clear dominant language. Require both high diversity and no clear majority.
    return dominant_share < 0.72 and counted / total > 0.82
