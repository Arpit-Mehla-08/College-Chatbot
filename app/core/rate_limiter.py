"""Simple in-memory rate limiter."""

import time
from collections import defaultdict

from app.core.config import settings


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window.

    Limits requests per conversation/session within a time window.
    """

    def __init__(self, max_requests: int | None = None, window_seconds: int = 60):
        self._max_requests = max_requests or settings.RATE_LIMIT_PER_MINUTE
        self._window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """
        Check if a request is allowed for the given key.

        Args:
            key: Rate limit key (e.g., conversation_id or IP)

        Returns:
            True if allowed, False if rate limited.
        """
        now = time.time()
        window_start = now - self._window_seconds

        # Clean old entries
        self._requests[key] = [
            t for t in self._requests[key] if t > window_start
        ]

        # Check limit
        if len(self._requests[key]) >= self._max_requests:
            return False

        # Record this request
        self._requests[key].append(now)
        return True

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key."""
        now = time.time()
        window_start = now - self._window_seconds
        current = len([t for t in self._requests[key] if t > window_start])
        return max(0, self._max_requests - current)

    def clear(self) -> None:
        """Clear all rate limit data."""
        self._requests.clear()


# Singleton
rate_limiter = RateLimiter()
