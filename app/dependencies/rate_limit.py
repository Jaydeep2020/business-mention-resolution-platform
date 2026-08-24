from fastapi import (
    Depends,
    HTTPException,
    status,
)

from app.core.rate_limit import (
    resolution_rate_limiter,
)

from app.dependencies.auth import (
    get_current_user,
)

from app.models.user import User


def resolution_rate_limit(
    current_user: User = Depends(
        get_current_user
    ),
) -> None:
    """
    Apply per-user rate limiting to the
    business resolution endpoint.
    """

    # Each logged-in user gets a separate counter.
    #
    # Example:
    #
    # user:1
    # user:2
    # user:3

    key = (
        f"user:{current_user.id}"
    )

    result = (
        resolution_rate_limiter.check(
            key
        )
    )

    if not result.allowed:

        raise HTTPException(
            status_code=(
                status.HTTP_429_TOO_MANY_REQUESTS
            ),
            detail=(
                "Too many resolution requests. "
                f"Try again in approximately "
                f"{result.retry_after} seconds."
            ),
            headers={
                "Retry-After": str(
                    result.retry_after
                ),
                "X-RateLimit-Limit": str(
                    resolution_rate_limiter
                    .request_limit
                ),
                "X-RateLimit-Remaining": "0",
            },
        )

    return None