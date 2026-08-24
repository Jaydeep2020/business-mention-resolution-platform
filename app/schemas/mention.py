from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    ResolutionStatus,
    SourceType,
)


class MentionCreate(BaseModel):

    text: str = Field(
        min_length=1,
        max_length=255,
    )

    source_text: str | None = None

    source_type: SourceType = SourceType.REVIEW

    source_id: str | None = Field(
        default=None,
        max_length=100,
    )


class MentionUpdate(BaseModel):

    text: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    source_text: str | None = None

    source_type: SourceType | None = None

    source_id: str | None = Field(
        default=None,
        max_length=100,
    )


class MentionResponse(BaseModel):

    id: int

    text: str

    source_text: str | None

    source_type: SourceType

    source_id: str | None

    resolved_business_id: int | None

    resolution_status: ResolutionStatus

    confidence_score: float | None

    model_config = ConfigDict(
        from_attributes=True
    )


class MentionListResponse(BaseModel):

    items: list[MentionResponse]

    page: int
    page_size: int
    total: int
    total_pages: int