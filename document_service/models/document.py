# document_service/models/document.py

from datetime import datetime

from sqlalchemy import (
    DateTime,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from document_service.models.base import Base


class Document(Base):

    __tablename__ = "documents"

    # "summary" or "monthly_report"
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    month: Mapped[str | None] = mapped_column(
        String(7),
        nullable=True,
    )