# This should mirror the contract from catalog service.

from pydantic import (
    BaseModel,
    Field,
)


class ResolutionCandidatePayload(
    BaseModel
):

    business_name: str

    city: str | None = None

    score: float = Field(
        ge=0,
        le=1,
    )

    is_verified: bool

    decision: str


class ResolvedBusinessPayload(
    BaseModel
):

    business_id: str

    name: str

    address: str | None = None

    city: str | None = None

    state: str | None = None

    postal_code: str | None = None

    is_verified: bool


class ResolutionSummaryPayload(
    BaseModel
):

    mention_id: int

    mention_text: str

    source_type: str | None = None

    source_id: str | None = None

    source_text: str | None = None

    resolution_status: str

    decision: str | None = None

    confidence_score: float | None = None

    resolved_business_id: int | None = None

    reviewer_username: str | None = None

    reviewer_notes: str | None = None

    decision_notes: str | None = None

    resolved_business: (
        ResolvedBusinessPayload
        | None
    ) = None

    candidates: list[
        ResolutionCandidatePayload
    ] = []


class ReviewReasonPayload(
    BaseModel
):

    reason: str

    count: int


class MonthlyReportPayload(
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
        ReviewReasonPayload
    ] = []