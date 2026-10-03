"""محدودکننده‌ی ساده‌ی نرخ برای endpoint عمومی ویجت (per-process)."""
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from .. import config


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = max(1, limit)
        self.window_seconds = max(1, window_seconds)
        self._events = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now)
            if len(self._events) > 2048:
                self._evict_old(now)
            return True

    def _evict_old(self, now: float) -> None:
        cutoff = now - self.window_seconds
        stale = [key for key, events in self._events.items() if not events or events[-1] <= cutoff]
        for key in stale:
            self._events.pop(key, None)


public_widget_limiter = RateLimiter(config.PUBLIC_WIDGET_RATE_LIMIT, config.PUBLIC_WIDGET_RATE_WINDOW_SECONDS)
