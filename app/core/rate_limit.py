from collections import defaultdict, deque
from dataclasses import dataclass
from math import ceil
from threading import Lock
from time import monotonic

from app.core.config import settings


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after: int


class InMemoryRateLimiter:
    """
    Simple in-memory sliding-window rate limiter.

    Example:

    limit = 10
    window = 60 seconds

    Each user can make at most 10 requests
    during any 60-second window.
    """

    def __init__(
        self,
        request_limit: int,
        window_seconds: int,
    ):

        if request_limit < 1:
            raise ValueError(
                "request_limit must be at least 1"
            )

        if window_seconds < 1:
            raise ValueError(
                "window_seconds must be at least 1"
            )

        self.request_limit = request_limit

        self.window_seconds = window_seconds

        # Example:
        #
        # {
        #     "user:5": deque([time1, time2, ...]),
        #     "user:10": deque([...])
        # }
        self._requests = defaultdict(deque)

        # Protect dictionary/deques when multiple requests
        # arrive at the same time.
        self._lock = Lock()

    def check(
        self,
        key: str,
    ) -> RateLimitResult:
        """
        Check and consume one request for this key.
        """

        now = monotonic()

        cutoff = (
            now
            - self.window_seconds
        )

        with self._lock:

            request_times = (
                self._requests[key]
            )

            # Remove requests that are older than
            # the current rate-limit window.
            while (
                request_times
                and request_times[0] <= cutoff
            ):

                request_times.popleft()

            # ------------------------------------------------
            # Limit reached
            # ------------------------------------------------

            if (
                len(request_times)
                >= self.request_limit
            ):

                oldest_request = (
                    request_times[0]
                )

                retry_after = ceil(
                    self.window_seconds
                    - (
                        now
                        - oldest_request
                    )
                )

                retry_after = max(
                    1,
                    retry_after,
                )

                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    retry_after=retry_after,
                )

            # ------------------------------------------------
            # Request is allowed
            # ------------------------------------------------

            request_times.append(
                now
            )

            remaining = (
                self.request_limit
                - len(request_times)
            )

            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                retry_after=0,
            )

    def reset(
        self,
        key: str,
    ) -> None:
        """
        Remove rate-limit history for one key.

        Mainly useful in tests.
        """

        with self._lock:

            self._requests.pop(
                key,
                None,
            )

    def clear(self) -> None:
        """
        Remove rate-limit history for everybody.

        Mainly useful in tests.
        """

        with self._lock:

            self._requests.clear()


# ==========================================================
# RESOLUTION ENDPOINT LIMITER
# ==========================================================

resolution_rate_limiter = (
    InMemoryRateLimiter(
        request_limit=(
            settings
            .RESOLUTION_RATE_LIMIT_REQUESTS
        ),
        window_seconds=(
            settings
            .RESOLUTION_RATE_LIMIT_WINDOW_SECONDS
        ),
    )
)