from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.business import Business
from app.models.category import Category
from app.models.mention import Mention
from app.models.resolution_result import ResolutionResult

from app.schemas.business import (
    BusinessCreate,
    BusinessUpdate,
)


class BusinessService:

    @staticmethod
    def create_business(
        session: Session,
        data: BusinessCreate,
    ) -> Business:

        existing_business = (
            session.execute(
                select(Business)
                .where(
                    Business.business_id
                    == data.business_id
                )
            )
            .scalar_one_or_none()
        )

        if existing_business:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Business with this business_id already exists",
            )

        categories = []

        if data.category_ids:

            categories = list(
                session.execute(
                    select(Category)
                    .where(
                        Category.id.in_(
                            data.category_ids
                        )
                    )
                )
                .scalars()
                .all()
            )

            found_ids = {
                category.id
                for category in categories
            }

            missing_ids = set(data.category_ids) - found_ids

            if missing_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Categories not found: "
                        f"{sorted(missing_ids)}"
                    ),
                )

        business = Business(
            business_id=data.business_id,
            name=data.name,
            address=data.address,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            latitude=data.latitude,
            longitude=data.longitude,
            is_verified=data.is_verified,
        )

        business.categories = categories

        try:
            session.add(business)
            session.commit()
            session.refresh(business)

        except Exception:
            session.rollback()
            raise

        return business

    @staticmethod
    def get_business(
        session: Session,
        business_pk: int,
    ) -> Business:

        stmt = (
            select(Business)
            .options(
                selectinload(Business.categories)
            )
            .where(
                Business.id == business_pk
            )
        )

        business = session.execute(
            stmt
        ).scalar_one_or_none()

        if business is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found",
            )

        return business

    @staticmethod
    def get_businesses(
        session: Session,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        city: str | None = None,
        category_id: int | None = None,
        is_verified: bool | None = None,
    ):

        if page < 1:
            page = 1

        if page_size < 1:
            page_size = 20

        if page_size > 100:
            page_size = 100

        conditions = []

        if search:

            search_value = f"%{search.strip()}%"

            conditions.append(
                or_(
                    Business.name.ilike(search_value),
                    Business.business_id.ilike(
                        search_value
                    ),
                    Business.address.ilike(
                        search_value
                    ),
                )
            )

        if city:

            conditions.append(
                Business.city.ilike(
                    f"%{city.strip()}%"
                )
            )

        if is_verified is not None:

            conditions.append(
                Business.is_verified
                == is_verified
            )

        if category_id is not None:

            stmt = (
                select(Business)
                .join(
                    Business.categories
                )
                .where(
                    Category.id == category_id
                )
            )

        else:

            stmt = select(Business)

        if conditions:

            stmt = stmt.where(
                *conditions
            )

        stmt = stmt.options(
            selectinload(Business.categories)
        )

        total_stmt = (
            select(
                func.count(
                    func.distinct(
                        Business.id
                    )
                )
            )
        )

        if category_id is not None:

            total_stmt = (
                total_stmt
                .join(
                    Business.categories
                )
                .where(
                    Category.id
                    == category_id
                )
            )

        if conditions:

            total_stmt = total_stmt.where(
                *conditions
            )

        total = session.execute(
            total_stmt
        ).scalar_one()

        offset = (
            page - 1
        ) * page_size

        stmt = (
            stmt
            .order_by(Business.name.asc())
            .offset(offset)
            .limit(page_size)
        )

        businesses = list(
            session.execute(stmt)
            .scalars()
            .unique()
            .all()
        )

        total_pages = (
            ceil(total / page_size)
            if total
            else 0
        )

        return {
            "items": businesses,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }

    @staticmethod
    def update_business(
        session: Session,
        business_pk: int,
        data: BusinessUpdate,
    ) -> Business:

        business = (
            session.execute(
                select(Business)
                .options(
                    selectinload(
                        Business.categories
                    )
                )
                .where(
                    Business.id
                    == business_pk
                )
            )
            .scalar_one_or_none()
        )

        if business is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found",
            )

        update_data = data.model_dump(
            exclude_unset=True
        )

        category_ids = update_data.pop(
            "category_ids",
            None,
        )

        for field, value in update_data.items():

            setattr(
                business,
                field,
                value,
            )

        if category_ids is not None:

            categories = list(
                session.execute(
                    select(Category)
                    .where(
                        Category.id.in_(
                            category_ids
                        )
                    )
                )
                .scalars()
                .all()
            )

            found_ids = {
                category.id
                for category in categories
            }

            missing_ids = (
                set(category_ids)
                - found_ids
            )

            if missing_ids:

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Categories not found: "
                        f"{sorted(missing_ids)}"
                    ),
                )

            business.categories = categories

        try:

            session.commit()
            session.refresh(business)

        except Exception:

            session.rollback()
            raise

        return business

    @staticmethod
    def delete_business(
        session: Session,
        business_pk: int,
    ) -> None:

        business = (
            session.execute(
                select(Business)
                .where(
                    Business.id
                    == business_pk
                )
            )
            .scalar_one_or_none()
        )

        if business is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found",
            )

        mention_exists = (
            session.execute(
                select(Mention.id)
                .where(
                    Mention.resolved_business_id
                    == business_pk
                )
                .limit(1)
            )
            .scalar_one_or_none()
        )

        resolution_exists = (
            session.execute(
                select(ResolutionResult.id)
                .where(
                    ResolutionResult.business_id
                    == business_pk
                )
                .limit(1)
            )
            .scalar_one_or_none()
        )

        if (
            mention_exists is not None
            or resolution_exists is not None
        ):

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Business cannot be deleted because "
                    "it is referenced by mentions or "
                    "resolution results."
                ),
            )

        try:

            session.delete(business)
            session.commit()

        except Exception:

            session.rollback()
            raise