import httpx

from fastapi import (
    HTTPException,
    status,
)

from document_service.core.config import (
    settings,
)


class CatalogClient:

    @staticmethod
    def _headers() -> dict:

        return {
            "X-Internal-Service-Key": (
                settings
                .INTERNAL_SERVICE_TOKEN
            )
        }


    @staticmethod
    def _handle_response(
        response: httpx.Response,
    ) -> dict:

        if response.is_success:

            return response.json()

        try:

            body = response.json()

            detail = body.get(
                "detail",
                "Catalog Service request failed.",
            )

        except Exception:

            detail = (
                "Catalog Service request failed."
            )

        if (
            400
            <= response.status_code
            < 500
        ):

            raise HTTPException(
                status_code=(
                    response.status_code
                ),
                detail=detail,
            )

        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),
            detail=(
                "Catalog Service returned "
                "an unexpected error."
            ),
        )


    # ======================================================
    # RESOLUTION SNAPSHOT
    # ======================================================

    @classmethod
    def get_resolution_snapshot(
        cls,
        mention_id: int,
    ) -> dict:

        url = (
            f"{settings.CATALOG_SERVICE_URL}"
            f"/internal/resolutions/"
            f"{mention_id}/snapshot"
        )

        try:

            with httpx.Client(
                timeout=(
                    settings
                    .SERVICE_HTTP_TIMEOUT_SECONDS
                )
            ) as client:

                response = client.get(
                    url,
                    headers=(
                        cls._headers()
                    ),
                )

        except httpx.RequestError as exc:

            raise HTTPException(
                status_code=(
                    status
                    .HTTP_503_SERVICE_UNAVAILABLE
                ),
                detail=(
                    "Catalog Service "
                    "is unavailable."
                ),
            ) from exc

        return cls._handle_response(
            response
        )


    # ======================================================
    # MONTHLY REPORT DATA
    # ======================================================

    @classmethod
    def get_monthly_report_data(
        cls,
        month: str,
    ) -> dict:

        url = (
            f"{settings.CATALOG_SERVICE_URL}"
            f"/internal/reporting/monthly/"
            f"{month}"
        )

        try:

            with httpx.Client(
                timeout=(
                    settings
                    .SERVICE_HTTP_TIMEOUT_SECONDS
                )
            ) as client:

                response = client.get(
                    url,
                    headers=(
                        cls._headers()
                    ),
                )

        except httpx.RequestError as exc:

            raise HTTPException(
                status_code=(
                    status
                    .HTTP_503_SERVICE_UNAVAILABLE
                ),
                detail=(
                    "Catalog Service "
                    "is unavailable."
                ),
            ) from exc

        return cls._handle_response(
            response
        )