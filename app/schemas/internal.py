from pydantic import BaseModel


# ==========================================================
# RESOLUTION SNAPSHOT
# ==========================================================

class ResolvedBusinessSnapshot(
    BaseModel
):

    business_id: str

    name: str

    address: str | None

    city: str | None

    state: str | None

    postal_code: str | None

    is_verified: bool


class CandidateSnapshot(
    BaseModel
):

    business_name: str

    city: str | None

    score: float

    is_verified: bool

    decision: str


class ResolutionSnapshotResponse(
    BaseModel
):

    mention_id: int

    mention_text: str

    source_type: str | None

    source_id: str | None

    source_text: str | None

    resolution_status: str

    decision: str | None

    confidence_score: float | None

    resolved_business_id: int | None

    reviewer_username: str | None

    reviewer_notes: str | None

    decision_notes: str | None

    resolved_business: (
        ResolvedBusinessSnapshot
        | None
    )

    candidates: list[
        CandidateSnapshot
    ]


# ==========================================================
# MONTHLY REPORT
# ==========================================================

class ReviewReasonData(BaseModel):

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
        ReviewReasonData
    ]