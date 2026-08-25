from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ==========================================================
# API REQUEST
# ==========================================================

class AssistantResolveRequest(
    BaseModel
):

    max_candidates: int = Field(
        default=5,
        ge=2,
        le=10,
        strict=True,
    )

    model_config = ConfigDict(
        extra="forbid"
    )


# ==========================================================
# LLM STRUCTURED DECISION
# ==========================================================

class AssistantRecommendation(
    BaseModel
):
    """
    Structured result returned by the LLM.

    The LLM cannot directly change the database.
    This result is validated by Python before
    anything is resolved.
    """

    action: Literal[
        "resolve",
        "escalate",
    ]

    selected_business_id: int | None = (
        None
    )

    confidence: float = Field(
        ge=0,
        le=1,
    )

    note: str = Field(
        min_length=5,
        max_length=2000,
    )

    model_config = ConfigDict(
        extra="forbid"
    )


# ==========================================================
# CANDIDATE
# ==========================================================

class AssistantCandidateResponse(
    BaseModel
):

    business_id: int

    catalog_business_id: str

    business_name: str

    city: str | None

    state: str | None

    address: str | None

    categories: list[str] = []

    is_verified: bool

    score: float = Field(
        ge=0,
        le=1,
    )

    name_score: float = Field(
        ge=0,
        le=1,
    )

    embedding_score: float | None = Field(
        default=None,
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


# ==========================================================
# FINAL RESPONSE
# ==========================================================

class AssistantResolutionResponse(
    BaseModel
):

    mention_id: int

    mention_text: str

    action: Literal[
        "resolved",
        "escalated",
    ]

    decision_source: Literal[
        "rule",
        "policy",
        "llm",
    ]

    resolution_status: str

    resolved_business_id: int | None

    recommended_business_id: int | None

    candidate_score: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    assistant_confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    ambiguous: bool

    score_gap: float | None

    note: str

    document_id: int | None = None

    workflow_steps: list[str]

    candidates: list[
        AssistantCandidateResponse
    ]