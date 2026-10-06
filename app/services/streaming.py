"""ابزار مشترک پاسخ‌های استریم (Server-Sent Events) برای چت."""
import json
from typing import Iterable, Iterator, List, Optional, Tuple

from .. import models

# هدرهایی که مانع بافر شدن پاسخ در پروکسی/CDN (مثل Vercel و nginx) می‌شوند
SSE_HEADERS = {
    "Cache-Control": "no-store, no-cache, no-transform, private",
    "Pragma": "no-cache",
    "Expires": "0",
    "X-Robots-Tag": "noindex, noarchive, nosnippet",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def sse(event: str, data: Optional[dict] = None) -> str:
    payload = json.dumps(data or {}, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def sources_payload(matches: List[Tuple[models.Chunk, float]]) -> List[dict]:
    """منابع بازیابی‌شده را پیش از شروع استریم (وقتی نشست دیتابیس هنوز باز است) سریالایز می‌کند."""
    return [
        {"document_title": chunk.document.title, "text": chunk.text, "score": round(score, 4)}
        for chunk, score in matches
    ]


def relay_model_stream(
    pieces: Iterable[str], collected: List[str], on_first_delta=None
) -> Iterator[str]:
    """تکه‌های مدل را به رویدادهای delta تبدیل می‌کند و متن کامل را در collected نگه می‌دارد."""
    first = True
    for piece in pieces:
        collected.append(piece)
        if first and on_first_delta:
            on_first_delta()
        first = False
        yield sse("delta", {"t": piece})
