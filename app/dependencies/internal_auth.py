import secrets

from fastapi import (
    Header,
    HTTPException,
    status,
)

from app.core.config import settings


def verify_internal_service(
    x_internal_service_key: str | None = Header(
        default=None,
        alias="X-Internal-Service-Key",
    ),
) -> None:

    expected = (
        settings.INTERNAL_SERVICE_TOKEN
    )

    if (
        not x_internal_service_key
        or not secrets.compare_digest(
            x_internal_service_key,
            expected,
        )
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid internal service credentials."
            ),
        )