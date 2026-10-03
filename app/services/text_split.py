"""
تکه‌تکه‌کردن (Chunking) متن اسناد دانشنامه قبل از امبد کردن.
پیاده‌سازی ساده و بدون وابستگی خارجی: ابتدا بر اساس پاراگراف می‌شکند و بعد
پاراگراف‌ها را در بسته‌هایی با طول حداکثر CHUNK_SIZE (با کمی همپوشانی برای
حفظ سیاق جمله‌ها بین تکه‌ها) کنار هم می‌چیند.
"""
from typing import List

from .. import config


def split_text(
    text: str,
    chunk_size: int = config.CHUNK_SIZE,
    overlap: int = config.CHUNK_OVERLAP,
) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []

    # گام ۱: هر پاراگراف بسیار بزرگ را از قبل با یک پنجره‌ی لغزان ساده می‌شکنیم
    # تا در گام بعد هیچ‌وقت با یک تکه‌ی بزرگ‌تر از chunk_size روبه‌رو نشویم.
    raw_paragraphs = [p.strip() for p in text.replace("\r\n", "\n").split("\n") if p.strip()]
    if not raw_paragraphs:
        raw_paragraphs = [text]

    pieces: List[str] = []
    for para in raw_paragraphs:
        if len(para) <= chunk_size:
            pieces.append(para)
            continue
        start = 0
        step = max(chunk_size - overlap, 1)
        while start < len(para):
            pieces.append(para[start:start + chunk_size])
            start += step

    # گام ۲: تکه‌های کوچک را در بسته‌هایی تا سقف chunk_size کنار هم می‌چینیم
    chunks: List[str] = []
    current = ""
    for piece in pieces:
        candidate = f"{current}\n{piece}".strip() if current else piece
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = piece

    if current:
        chunks.append(current)

    return [c for c in chunks if c.strip()]
