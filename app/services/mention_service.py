from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.mention import Mention
from app.models.enums import ResolutionStatus

from app.schemas.mention import (
    MentionCreate,
    MentionUpdate,
)


class MentionService:

    @staticmethod
    def create_mention(
        session: Session,
        data: MentionCreate,
    ) -> Mention:

        mention = Mention(
            text=data.text.strip(),
            source_text=data.source_text,
            source_type=data.source_type,
            source_id=data.source_id,
        )

        try:
            session.add(mention)
            session.commit()
            session.refresh(mention)

        except Exception:
            session.rollback()
            raise

        return mention

    @staticmethod
    def get_mention(
        session: Session,
        mention_id: int,
    ) -> Mention:

        stmt = (
            select(Mention)
            .where(
                Mention.id == mention_id
            )
        )

        mention = (
            session.execute(stmt)
            .scalar_one_or_none()
        )

        if mention is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mention not found",
            )

        return mention

    @staticmethod
    def get_mentions(
        session: Session,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status_filter: ResolutionStatus | None = None,
    ):

        if page < 1:
            page = 1

        if page_size < 1:
            page_size = 20

        if page_size > 100:
            page_size = 100

        conditions = []

        if search:

            search_value = (
                f"%{search.strip()}%"
            )

            conditions.append(
                Mention.text.ilike(
                    search_value
                )
            )

        if status_filter is not None:

            conditions.append(
                Mention.resolution_status
                == status_filter
            )

        # Count
        count_stmt = select(
            func.count(Mention.id)
        )

        if conditions:
            count_stmt = count_stmt.where(
                *conditions
            )

        total = (
            session.execute(count_stmt)
            .scalar_one()
        )

        # Data
        stmt = select(Mention)

        if conditions:
            stmt = stmt.where(
                *conditions
            )

        offset = (
            page - 1
        ) * page_size

        stmt = (
            stmt
            .order_by(Mention.id.desc())
            .offset(offset)
            .limit(page_size)
        )

        mentions = list(
            session.execute(stmt)
            .scalars()
            .all()
        )

        total_pages = (
            ceil(total / page_size)
            if total > 0
            else 0
        )

        return {
            "items": mentions,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }

    @staticmethod
    def update_mention(
        session: Session,
        mention_id: int,
        data: MentionUpdate,
    ) -> Mention:

        mention = (
            session.execute(
                select(Mention)
                .where(
                    Mention.id == mention_id
                )
            )
            .scalar_one_or_none()
        )

        if mention is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mention not found",
            )

        # Do not allow modifying a resolved
        # mention through normal update.
        if (
            mention.resolution_status
            != ResolutionStatus.PENDING
        ):

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Only pending mentions can be updated."
                ),
            )

        update_data = data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():

            if (
                isinstance(value, str)
                and field == "text"
            ):
                value = value.strip()

            setattr(
                mention,
                field,
                value,
            )

        try:

            session.commit()
            session.refresh(mention)

        except Exception:

            session.rollback()
            raise

        return mention

    @staticmethod
    def delete_mention(
        session: Session,
        mention_id: int,
    ) -> None:

        mention = (
            session.execute(
                select(Mention)
                .where(
                    Mention.id == mention_id
                )
            )
            .scalar_one_or_none()
        )

        if mention is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mention not found",
            )

        # Do not delete a mention after it has
        # already gone through the resolution flow.
        if (
            mention.resolution_status
            != ResolutionStatus.PENDING
        ):

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Resolved or reviewed mentions "
                    "cannot be deleted."
                ),
            )

        try:

            session.delete(mention)
            session.commit()

        except Exception:

            session.rollback()
            raise