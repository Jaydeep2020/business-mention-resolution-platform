from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.enums import UserRole

from app.core.security import (
    verify_password,
    create_access_token,
    hash_password,
)


class AuthService:

    @staticmethod
    def create_user(
        session: Session,
        username: str,
        password: str,
        role: UserRole = UserRole.VIEWER,
    ) -> User:

        # Check if username already exists
        stmt = (
            select(User)
            .where(User.username == username)
        )

        existing_user = (
            session.execute(stmt)
            .scalar_one_or_none()
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )

        # Hash password before storing
        password_hash = hash_password(password)

        user = User(
            username=username,
            password_hash=password_hash,
            role=role,
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        return user


    @staticmethod
    def authenticate_user(
        session: Session,
        username: str,
        password: str,
    ) -> User | None:

        stmt = (
            select(User)
            .where(User.username == username)
        )

        user = (
            session.execute(stmt)
            .scalar_one_or_none()
        )

        if user is None:
            return None

        if not verify_password(
            password,
            user.password_hash,
        ):
            return None

        return user


    @staticmethod
    def create_login_token(
        user: User,
    ) -> str:

        role = (
            user.role.value
            if hasattr(user.role, "value")
            else str(user.role)
        )

        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": role,
        }

        return create_access_token(
            token_data
        )