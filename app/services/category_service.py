from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.category import Category
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
)


class CategoryService:

    @staticmethod
    def create_category(
        session: Session,
        data: CategoryCreate,
    ) -> Category:

        existing_category = (
            session.execute(
                select(Category)
                .where(
                    func.lower(Category.name)
                    == data.name.strip().lower()
                )
            )
            .scalar_one_or_none()
        )

        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category already exists",
            )

        category = Category(
            name=data.name.strip()
        )

        try:
            session.add(category)
            session.commit()
            session.refresh(category)

        except Exception:
            session.rollback()
            raise

        return category

    @staticmethod
    def get_category(
        session: Session,
        category_id: int,
    ) -> Category:

        stmt = (
            select(Category)
            .where(Category.id == category_id)
        )

        category = (
            session.execute(stmt)
            .scalar_one_or_none()
        )

        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        return category

    @staticmethod
    def get_categories(
        session: Session,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ):

        if page < 1:
            page = 1

        if page_size < 1:
            page_size = 20

        if page_size > 100:
            page_size = 100

        conditions = []

        if search:
            conditions.append(
                Category.name.ilike(
                    f"%{search.strip()}%"
                )
            )

        # Total count
        count_stmt = select(
            func.count(Category.id)
        )

        if conditions:
            count_stmt = count_stmt.where(
                *conditions
            )

        total = (
            session.execute(count_stmt)
            .scalar_one()
        )

        # Data query
        stmt = select(Category)

        if conditions:
            stmt = stmt.where(
                *conditions
            )

        offset = (page - 1) * page_size

        stmt = (
            stmt
            .order_by(Category.name.asc())
            .offset(offset)
            .limit(page_size)
        )

        categories = list(
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
            "items": categories,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }

    @staticmethod
    def update_category(
        session: Session,
        category_id: int,
        data: CategoryUpdate,
    ) -> Category:

        category = (
            session.execute(
                select(Category)
                .where(
                    Category.id == category_id
                )
            )
            .scalar_one_or_none()
        )

        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        new_name = data.name.strip()

        # Check another category does not
        # already have this name
        existing_category = (
            session.execute(
                select(Category)
                .where(
                    func.lower(Category.name)
                    == new_name.lower(),
                    Category.id != category_id,
                )
            )
            .scalar_one_or_none()
        )

        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category already exists",
            )

        category.name = new_name

        try:
            session.commit()
            session.refresh(category)

        except Exception:
            session.rollback()
            raise

        return category

    @staticmethod
    def delete_category(
        session: Session,
        category_id: int,
    ) -> None:

        category = (
            session.execute(
                select(Category)
                .where(
                    Category.id == category_id
                )
            )
            .scalar_one_or_none()
        )

        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

        # Because your category has a many-to-many
        # relationship with Business, SQLAlchemy can
        # remove the association rows when the
        # relationship is updated/deleted depending
        # on configuration.
        #
        # We prevent accidental deletion when the
        # category is still being used.

        if category.businesses:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Category cannot be deleted because "
                    "it is associated with businesses."
                ),
            )

        try:
            session.delete(category)
            session.commit()

        except Exception:
            session.rollback()
            raise