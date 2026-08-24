from typing import TYPE_CHECKING

from sqlalchemy import (CheckConstraint, Float, ForeignKey, Integer, String, Text, Enum as SQLEnum)
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.models.base import Base
from app.models.enums import ResolutionStatus, SourceType

class Mention(Base):
    __tablename__ = "mentions"

    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_mention_confidence_range",
        ),
    )

    # Extracted business mention
    # Example: "Tony's Pizza"
    text: Mapped[str] = mapped_column(String(255), nullable=False)

    # Full review text / surrounding context
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_type: Mapped[SourceType] = mapped_column(SQLEnum(SourceType, name="source_type_enum", native_enum=False, create_constraint=True), nullable=False, default=SourceType.REVIEW)

    #Example: Yelp review_id
    source_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Final business chosen after resolution
    resolved_business_id: Mapped[int | None] = mapped_column(ForeignKey("businesses.id"), nullable=True, index=True)

    resolution_status: Mapped[ResolutionStatus] = mapped_column(SQLEnum(ResolutionStatus, name="resolution_status_enum", native_enum=False, create_constraint=True), nullable=False, default=ResolutionStatus.PENDING, index=True)

    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)


    # Relationship

    resolved_business: Mapped["Business | None"] = relationship(
        "Business",
        back_populates="mentions",
    )

    resolution_results: Mapped[list["ResolutionResult"]] = relationship(
        "ResolutionResult",
        back_populates="mention",
        cascade="all, delete-orphan",
    )
