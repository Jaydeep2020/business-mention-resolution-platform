from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Document(Base):
    __tablename__ = "documents"

    # "summary" or "monthly_report"
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Example:
    # documents/resolution_123.pdf
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    # Example: "2026-08"
    # NULL for resolution summary
    month: Mapped[str | None] = mapped_column(
        String(7),
        nullable=True,
    )