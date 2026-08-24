from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.models.enums import (
    ResolutionDecision,
)


# ==========================================================
# RESOLVE REQUEST
# ==========================================================

class ResolveMentionRequest(BaseModel):

    max_candidates: int = Field(
        default=5,
        ge=1,
        le=20,
        strict=True,
        description=(
            "Maximum number of business candidates "
            "to consider during resolution."
        ),
    )

    model_config = ConfigDict(
        extra="forbid"
    )


# ==========================================================
# CANDIDATE RESPONSE
# ==========================================================

class CandidateResponse(BaseModel):

    business_id: int

    catalog_business_id: str

    business_name: str

    city: str | None

    state: str | None

    address: str | None

    score: float = Field(
        ge=0,
        le=1,
    )

    name_score: float = Field(
        ge=0,
        le=1,
    )

    city_score: float = Field(
        ge=0,
        le=1,
    )

    state_score: float = Field(
        ge=0,
        le=1,
    )

    address_score: float = Field(
        ge=0,
        le=1,
    )

    is_verified: bool


# ==========================================================
# RESOLUTION RESPONSE
# ==========================================================

class ResolutionResponse(BaseModel):

    mention_id: int

    mention_text: str

    resolution_status: str

    confidence_score: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    resolved_business_id: int | None

    document_id: int | None = None

    candidates: list[
        CandidateResponse
    ]


# ==========================================================
# RESOLUTION RESULT
# ==========================================================

class ResolutionResultResponse(BaseModel):

    id: int

    mention_id: int

    business_id: int

    score: float = Field(
        ge=0,
        le=1,
    )

    decision: ResolutionDecision

    reviewer_id: int | None

    notes: str | None

    model_config = ConfigDict(
        from_attributes=True
    )


class ResolutionResultListResponse(
    BaseModel
):

    items: list[
        ResolutionResultResponse
    ]

    page: int

    page_size: int

    total: int

    total_pages: int


# ==========================================================
# REVIEWER DECISION
# ==========================================================

class ReviewDecisionRequest(BaseModel):

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )

    model_config = ConfigDict(
        extra="forbid"
    )

    @field_validator(
        "notes"
    )
    @classmethod
    def clean_notes(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        # Convert:
        #
        # "     "
        #
        # into:
        #
        # None

        if not value:
            return None

        return value