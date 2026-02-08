"""
In-memory rate limiter with fixed-window counters.

Tracks request counts per partner across three time windows
(minute, hour, day). No external dependencies required.

For multi-worker deployments, swap with a Redis-backed implementation.
"""
import logging
import time
from dataclasses import dataclass

from fastapi import HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Window definitions: name → duration in seconds
WINDOWS = {
    "minute": 60,
    "hour": 3600,
    "day": 86400,
}


@dataclass
class WindowCounter:
    """Tracks request count within a fixed time window."""
    count: int
    window_start: float


class InMemoryRateLimiter:
    """Fixed-window rate limiter keyed by partner_id.

    Each partner gets independent counters per window (minute/hour/day).
    When a window expires, the counter resets automatically.
    A limit of 0 means unlimited for that window.
    """

    def __init__(self):
        self._counters: dict[str, WindowCounter] = {}

    def check_and_increment(
        self,
        partner_id: str,
        limits: dict[str, int],
    ) -> dict:
        """
        Check all windows and increment counters.

        Args:
            partner_id: Unique partner identifier.
            limits: {"minute": 60, "hour": 1000, "day": 10000}

        Returns:
            Dict with remaining counts per window.

        Raises:
            HTTPException(429) if any window limit is exceeded.
        """
        now = time.time()
        result = {}

        for window_name, window_seconds in WINDOWS.items():
            limit = limits.get(window_name, 0)
            if limit <= 0:
                continue  # 0 = unlimited

            key = f"{partner_id}:{window_name}"
            counter = self._counters.get(key)

            # Window expired or first request → reset
            if not counter or (now - counter.window_start) >= window_seconds:
                self._counters[key] = WindowCounter(count=1, window_start=now)
                result[window_name] = {
                    "limit": limit,
                    "remaining": limit - 1,
                    "reset": int(now + window_seconds),
                }
            elif counter.count >= limit:
                # Limit exceeded
                retry_after = max(1, int(counter.window_start + window_seconds - now))
                logger.warning(
                    f"Rate limit exceeded: partner={partner_id} "
                    f"window={window_name} limit={limit} retry_after={retry_after}s"
                )
                raise HTTPException(
                    status_code=429,
                    detail={
                        "message": f"Rate-Limit überschritten. Bitte warten Sie {retry_after} Sekunden.",
                        "limit": limit,
                        "window": window_name,
                        "retry_after_seconds": retry_after,
                    },
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(counter.window_start + window_seconds)),
                        "Retry-After": str(retry_after),
                    },
                )
            else:
                counter.count += 1
                result[window_name] = {
                    "limit": limit,
                    "remaining": limit - counter.count,
                    "reset": int(counter.window_start + window_seconds),
                }

        return result


# Module-level singleton (shared across all requests in the same process)
rate_limiter = InMemoryRateLimiter()
