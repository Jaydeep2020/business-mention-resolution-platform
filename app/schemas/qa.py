# This file defines both:
#
# 1) What the user sends.
# 2) What structured query plan the LLM is allowed to create.


from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# ==========================================================
# USER QUESTION
# ==========================================================

class CatalogQuestionRequest(BaseModel):

    question: str = Field(
        min_length=3,
        max_length=1000,
    )

    model_config = ConfigDict(
        extra="forbid"
    )

    @field_validator("question")
    @classmethod
    def clean_question(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if not value:

            raise ValueError(
                "Question cannot be empty."
            )

        return value


# ==========================================================
# LLM QUERY PLAN
# ==========================================================

class CatalogQueryPlan(BaseModel):
    """
    The LLM can ONLY produce one of these safe query plans.

    It does NOT generate SQL.
    """

    intent: Literal[
        "list_businesses",
        "count_businesses",
        "top_by_mentions",
        "business_details",
        "unsupported",
    ]

    business_name: str | None = None

    city: str | None = None

    state: str | None = None

    category: str | None = None

    is_verified: bool | None = None

    limit: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    needs_clarification: bool = False

    clarification_question: str | None = None


# ==========================================================
# BUSINESS REFERENCE
# ==========================================================

class QAReference(BaseModel):

    business_id: int

    catalog_business_id: str

    business_name: str

    city: str | None = None

    state: str | None = None

    mention_count: int | None = None


# ==========================================================
# FINAL RESPONSE
# ==========================================================

class CatalogQAResponse(BaseModel):

    question: str

    answer: str

    intent: str

    records_used: int

    references: list[QAReference] = []

    needs_clarification: bool = False

    clarification_question: str | None = None