from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Enum as SQLEnum,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import Base
from app.models.enums import UserRole


if TYPE_CHECKING:
    from app.models.resolution_result import ResolutionResult


class User(Base):

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SQLEnum(
            UserRole,
            name="user_role_enum",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
        default=UserRole.VIEWER,
    )

    resolution_results: Mapped[
        list["ResolutionResult"]
    ] = relationship(
        "ResolutionResult",
        back_populates="reviewer",
    )