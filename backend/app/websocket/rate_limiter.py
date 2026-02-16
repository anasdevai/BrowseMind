"""
Rate limiting for WebSocket connections.
Enforces 100 messages per minute per connection.
"""
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Optional

from app.config import settings


class RateLimiter:
    """
    Token bucket rate limiter for WebSocket connections.
    Limits messages to 100 per minute per connection.
    """

    def __init__(self, max_messages: int = None, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_messages: Maximum messages per window (default from settings)
            window_seconds: Time window in seconds (default 60)
        """
        self.max_messages = max_messages or settings.ws_rate_limit
        self.window_seconds = window_seconds

        # Message timestamps per connection: connection_id -> deque[timestamp]
        self._message_times: Dict[str, deque] = defaultdict(lambda: deque())

    def check_rate_limit(self, connection_id: str) -> tuple[bool, Optional[int]]:
        """
        Check if a connection has exceeded rate limit.

        Args:
            connection_id: Connection ID to check

        Returns:
            Tuple of (allowed: bool, retry_after_seconds: Optional[int])
            - allowed: True if message is allowed, False if rate limited
            - retry_after_seconds: Seconds to wait before retry (if rate limited)
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)

        # Get message times for this connection
        times = self._message_times[connection_id]

        # Remove timestamps outside the window
        while times and times[0] < cutoff:
            times.popleft()

        # Check if limit exceeded
        if len(times) >= self.max_messages:
            # Calculate retry time (when oldest message exits window)
            oldest = times[0]
            retry_after = int((oldest + timedelta(seconds=self.window_seconds) - now).total_seconds())
            return False, max(1, retry_after)

        # Record this message
        times.append(now)
        return True, None

    def reset(self, connection_id: str) -> None:
        """
        Reset rate limit for a connection.

        Args:
            connection_id: Connection ID to reset
        """
        if connection_id in self._message_times:
            del self._message_times[connection_id]

    def get_remaining(self, connection_id: str) -> int:
        """
        Get remaining messages allowed in current window.

        Args:
            connection_id: Connection ID

        Returns:
            Number of messages remaining
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)

        times = self._message_times[connection_id]

        # Remove old timestamps
        while times and times[0] < cutoff:
            times.popleft()

        return max(0, self.max_messages - len(times))

    def get_stats(self, connection_id: str) -> dict:
        """
        Get rate limit statistics for a connection.

        Args:
            connection_id: Connection ID

        Returns:
            Dictionary with rate limit stats
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)

        times = self._message_times[connection_id]

        # Remove old timestamps
        while times and times[0] < cutoff:
            times.popleft()

        return {
            "max_messages": self.max_messages,
            "window_seconds": self.window_seconds,
            "messages_in_window": len(times),
            "remaining": max(0, self.max_messages - len(times)),
            "reset_at": (times[0] + timedelta(seconds=self.window_seconds)).isoformat() if times else None
        }

    def cleanup_stale_connections(self, active_connection_ids: set) -> int:
        """
        Remove rate limit data for disconnected connections.

        Args:
            active_connection_ids: Set of currently active connection IDs

        Returns:
            Number of stale connections cleaned up
        """
        stale_ids = set(self._message_times.keys()) - active_connection_ids
        for connection_id in stale_ids:
            del self._message_times[connection_id]
        return len(stale_ids)


# Global rate limiter instance
_rate_limiter: RateLimiter = None


def get_rate_limiter() -> RateLimiter:
    """
    Get or create the global rate limiter instance.

    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
