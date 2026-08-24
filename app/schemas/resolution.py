from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import ResolutionDecision


class ResolveMentionRequest(BaseModel):
    # Maximum number of candidates that will be considered
    max_candidates: int = Field(
        default=5,
        ge=1,
        le=20,
    )


class CandidateResponse(BaseModel):
    business_id: int
    catalog_business_id: str
    business_name: str
    city: str | None
    state: str | None
    address: str | None

    score: float
    name_score: float
    city_score: float
    state_score: float
    address_score: float

    is_verified: bool


class ResolutionResponse(BaseModel):
    mention_id: int
    mention_text: str

    resolution_status: str
    confidence_score: float | None
    resolved_business_id: int | None

    candidates: list[CandidateResponse]


class ResolutionResultResponse(BaseModel):
    id: int

    mention_id: int
    business_id: int

    score: float
    decision: ResolutionDecision

    reviewer_id: int | None
    notes: str | None

    model_config = ConfigDict(
        from_attributes=True
    )


class ResolutionResultListResponse(BaseModel):
    items: list[ResolutionResultResponse]

    page: int
    page_size: int
    total: int
    total_pages: int


class ReviewDecisionRequest(BaseModel):
    notes: str | None = Field(
        default=None,
        max_length=2000,
    )