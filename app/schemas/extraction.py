from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.models.enums import (
    SourceType,
)


# ==========================================================
# EXTRACTION REQUEST
# ==========================================================

class ExtractMentionsRequest(
    BaseModel
):

    # Full review/write-up that will be analyzed.
    text: str = Field(
        min_length=1,
        max_length=20000,
        description=(
            "Free-form text from which "
            "business mentions will be extracted."
        ),
    )

    source_type: SourceType = (
        SourceType.REVIEW
    )

    # Example:
    # Yelp review_id
    source_id: str | None = Field(
        default=None,
        max_length=100,
    )

    # True:
    # actually insert Mention rows.
    #
    # False:
    # only preview what NLP detects.
    save_mentions: bool = True

    model_config = ConfigDict(
        extra="forbid"
    )

    @field_validator("text")
    @classmethod
    def clean_text(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if not value:

            raise ValueError(
                "text cannot be empty"
            )

        return value

    @field_validator("source_id")
    @classmethod
    def clean_source_id(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        return value


# ==========================================================
# ONE EXTRACTED MENTION
# ==========================================================

class ExtractedMentionResponse(
    BaseModel
):

    text: str

    # spaCy entity label.
    # For this implementation:
    # ORG
    label: str

    start_char: int

    end_char: int

    # Database Mention ID.
    #
    # None when:
    # save_mentions = false
    mention_id: int | None = None

    # True:
    # new Mention row was created.
    #
    # False:
    # preview only OR existing Mention reused.
    created: bool = False


# ==========================================================
# EXTRACTION RESPONSE
# ==========================================================

class ExtractionResponse(
    BaseModel
):

    source_id: str | None

    source_type: SourceType

    model: str

    saved: bool

    total_extracted: int

    created_count: int

    reused_count: int

    mentions: list[
        ExtractedMentionResponse
    ]