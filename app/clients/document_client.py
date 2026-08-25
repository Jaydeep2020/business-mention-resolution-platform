import logging

import httpx

from app.core.config import settings


logger = logging.getLogger(
    __name__
)


class DocumentClient:

    @classmethod
    def generate_resolution_summary(
        cls,
        mention_id: int,
    ) -> int | None:
        """
        Ask the separate Document Service to create
        the PDF.

        Important:
        Resolution has already been committed.

        Therefore a document-service outage should
        NOT roll back a successful resolution.
        """

        url = (
            f"{settings.DOCUMENT_SERVICE_URL}"
            "/internal/resolution-summary"
        )

        headers = {
            "X-Internal-Service-Key": (
                settings
                .INTERNAL_SERVICE_TOKEN
            )
        }

        try:

            with httpx.Client(
                timeout=(
                    settings
                    .SERVICE_HTTP_TIMEOUT_SECONDS
                )
            ) as client:

                response = client.post(
                    url,
                    headers=headers,
                    json={
                        "mention_id": (
                            mention_id
                        )
                    },
                )

            response.raise_for_status()

            data = response.json()

            return data.get(
                "id"
            )

        except Exception:

            logger.exception(
                (
                    "Document Service failed to "
                    "generate summary for mention %s"
                ),
                mention_id,
            )

            # Resolution remains successful.
            return None