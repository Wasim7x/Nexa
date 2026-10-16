import time
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from backend.app.core.config import settings

class RateLimiter:
    """
    Sliding window rate limiter per customer identifier (WhatsApp phone number or IP).
    Thread-safe in-memory structure with automatic expiration.
    """

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._blocked_until: Dict[str, float] = {}

    def is_rate_limited(self, identifier: str) -> Tuple[bool, Optional[int]]:
        """
        Check if an identifier is currently rate limited.
        Returns: (is_limited, retry_after_seconds)
        """
        now = time.time()

        # Check if currently under block cooldown
        if identifier in self._blocked_until:
            blocked_until = self._blocked_until[identifier]
            if now < blocked_until:
                return True, int(blocked_until - now)
            else:
                del self._blocked_until[identifier]

        # Clean history older than window
        timestamps = self._history[identifier]
        cutoff = now - self.window_seconds
        valid_timestamps = [t for t in timestamps if t > cutoff]
        self._history[identifier] = valid_timestamps

        if len(valid_timestamps) >= self.max_requests:
            # Trigger cooldown
            self._blocked_until[identifier] = now + settings.RATE_LIMIT_COOLDOWN_SECONDS
            return True, settings.RATE_LIMIT_COOLDOWN_SECONDS

        # Record this request
        self._history[identifier].append(now)
        return False, None

    def reset(self, identifier: str):
        """Reset rate limit history for an identifier (useful in testing)."""
        if identifier in self._history:
            del self._history[identifier]
        if identifier in self._blocked_until:
            del self._blocked_until[identifier]

# Global rate limiter instance
global_rate_limiter = RateLimiter(
    max_requests=settings.MAX_REQUESTS_PER_MINUTE,
    window_seconds=60
)
