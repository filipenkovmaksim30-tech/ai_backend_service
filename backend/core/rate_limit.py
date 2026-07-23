import asyncio
import math
from collections import defaultdict, deque
from time import monotonic


class InMemoryRateLimiter:
    def __init__(self, *, max_requests: int, window_seconds: int) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()
        self._last_cleanup = monotonic()

    async def check(self, key: str) -> int | None:
        now = monotonic()
        cutoff = now - self._window_seconds

        async with self._lock:
            self._cleanup(now, cutoff)
            timestamps = self._requests[key]
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            if len(timestamps) >= self._max_requests:
                retry_after = self._window_seconds - (now - timestamps[0])
                return max(1, math.ceil(retry_after))

            timestamps.append(now)
            return None

    def _cleanup(self, now: float, cutoff: float) -> None:
        if now - self._last_cleanup < self._window_seconds:
            return

        expired_keys = [
            key
            for key, timestamps in self._requests.items()
            if not timestamps or timestamps[-1] <= cutoff
        ]
        for key in expired_keys:
            del self._requests[key]
        self._last_cleanup = now
