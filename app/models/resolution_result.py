from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ResolutionDecision

class ResolutionResult(Base):
    __tablename__ = "resolution_results"

    __table_args__ = (
        CheckConstraint(
            "score >= 0 AND score <= 1",
            name="ck_resolution_score_range",
        ),
    )

    mention_id : Mapped[int] = mapped_column(ForeignKey("mentions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Candidate business
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)

    score: Mapped[float] = mapped_column(Float, nullable=False)

    decision: Mapped[ResolutionDecision] = mapped_column(SQLEnum(ResolutionDecision, name="resolution_decision_enum", native_enum=False, create_constraint=True), nullable=False, index=True)

    # Filled when a human reviewer handles the result
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


    # Relationship

    mention: Mapped["Mention"] = relationship(
        "Mention",
        back_populates="resolution_results",
    )

    business: Mapped["Business"] = relationship(
        "Business",
        back_populates="resolution_results",
    )

    reviewer: Mapped["User | None"] = relationship(
        "User",
        back_populates="resolution_results",
    )