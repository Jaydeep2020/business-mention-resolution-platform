from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class DocumentResponse(
    BaseModel
):

    id: int

    type: str

    file_path: str

    generated_at: datetime

    month: str | None

    model_config = ConfigDict(
        from_attributes=True
    )


class DocumentListResponse(
    BaseModel
):

    items: list[
        DocumentResponse
    ]

    page: int

    page_size: int

    total: int

    total_pages: int


# ==========================================================
# INTERNAL SUMMARY REQUEST
# ==========================================================

class ResolutionSummaryRequest(
    BaseModel
):

    mention_id: int = Field(
        gt=0
    )

    model_config = ConfigDict(
        extra="forbid"
    )


# ==========================================================
# MONTH
# ==========================================================

class MonthlyReportRequest(
    BaseModel
):

    month: str = Field(
        examples=[
            "2026-08"
        ]
    )

    @field_validator(
        "month"
    )
    @classmethod
    def validate_month(
        cls,
        value: str,
    ) -> str:

        try:

            datetime.strptime(
                value,
                "%Y-%m",
            )

        except ValueError:

            raise ValueError(
                (
                    "month must be "
                    "in YYYY-MM format"
                )
            )

        return value


class ReviewReasonResponse(
    BaseModel
):

    reason: str

    count: int


class MonthlyReportDataResponse(
    BaseModel
):

    month: str

    mentions_processed: int

    auto_resolved: int

    reviewer_approved: int

    rejected: int

    sent_for_review: int

    match_rate: float

    review_reasons: list[
        ReviewReasonResponse
    ]


class MonthlyReportResponse(
    BaseModel
):

    document: (
        DocumentResponse
    )

    report: (
        MonthlyReportDataResponse
    )