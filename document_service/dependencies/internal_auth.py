import secrets

from fastapi import (
    Header,
    HTTPException,
    status,
)

from document_service.core.config import (
    settings,
)


def verify_internal_service(
    x_internal_service_key: str | None = Header(
        default=None,
        alias="X-Internal-Service-Key",
    ),
):

    if (
        not x_internal_service_key
        or not secrets.compare_digest(
            x_internal_service_key,
            settings.INTERNAL_SERVICE_TOKEN,
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