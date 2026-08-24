from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from .business import Business

class Category(Base):
    __tablename__ = 'categories'

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)


    # Relationship

    businesses : Mapped[list['Business']] = relationship(
        "Business",
        secondary="business_category",
        back_populates="categories",
    )