from typing import TYPE_CHECKING
from sqlalchemy import (Boolean, CheckConstraint, Float, Integer, JSON, String,)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from .category import Category
    from .mention import Mention
    from .resolution_result import ResolutionResult

class Business(Base):
    __tablename__ = 'businesses'

    business_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean,default=True, nullable=False)


    # Relationships
    categories: Mapped[list["Category"]] = relationship(
        "Category",
        secondary="business_category",
        back_populates="businesses",
    )

    # reviews: Mapped[list["Review"]] = relationship(
    #     "Review",
    #     back_populates="business",
    #     cascade="all, delete-orphan",
    # )

    mentions: Mapped[list["Mention"]] = relationship(
        "Mention",
        back_populates="resolved_business",
    )

    resolution_results: Mapped[list["ResolutionResult"]] = relationship(
        "ResolutionResult",
        back_populates="business",
    )