from pathlib import Path

import pytest

from sqlalchemy import (
    create_engine,
    event,
)

from sqlalchemy.orm import (
    sessionmaker,
)

from sqlalchemy.pool import StaticPool


# ==========================================================
# IMPORTANT:
# Import every model before Base.metadata.create_all()
#
# SQLAlchemy needs all tables/relationships registered.
# ==========================================================

from app.models.base import Base

from app.models.business import Business
from app.models.category import Category
from app.models.business_category import BusinessCategory
from app.models.mention import Mention
from app.models.resolution_result import ResolutionResult
from app.models.document import Document
from app.models.user import User

from app.models.enums import (
    ResolutionStatus,
    SourceType,
    UserRole,
)

from app.services.document_service import (
    DocumentService,
)


# ==========================================================
# TEST DATABASE ENGINE
# ==========================================================

@pytest.fixture()
def test_engine():

    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    # Enable foreign keys in SQLite.
    @event.listens_for(
        engine,
        "connect",
    )
    def enable_sqlite_foreign_keys(
        dbapi_connection,
        connection_record,
    ):

        cursor = (
            dbapi_connection.cursor()
        )

        cursor.execute(
            "PRAGMA foreign_keys=ON"
        )

        cursor.close()

    Base.metadata.create_all(
        bind=engine
    )

    yield engine

    Base.metadata.drop_all(
        bind=engine
    )

    engine.dispose()


# ==========================================================
# DATABASE SESSION
# ==========================================================

@pytest.fixture()
def db_session(
    test_engine,
):

    TestSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    session = TestSessionLocal()

    try:

        yield session

    finally:

        session.close()


# ==========================================================
# BUSINESS FACTORY
# ==========================================================

@pytest.fixture()
def business_factory(
    db_session,
):

    counter = 0

    def create_business(
        **overrides,
    ):

        nonlocal counter

        counter += 1

        data = {
            "business_id": (
                f"test-business-{counter}"
            ),
            "name": (
                f"Test Business {counter}"
            ),
            "address": (
                f"{counter} Main Street"
            ),
            "city": "Tucson",
            "state": "AZ",
            "postal_code": "85711",
            "latitude": 32.223236,
            "longitude": -110.880452,
            "is_verified": True,
        }

        data.update(
            overrides
        )

        business = Business(
            **data
        )

        db_session.add(
            business
        )

        db_session.commit()

        db_session.refresh(
            business
        )

        return business

    return create_business


# ==========================================================
# MENTION FACTORY
# ==========================================================

@pytest.fixture()
def mention_factory(
    db_session,
):

    counter = 0

    def create_mention(
        **overrides,
    ):

        nonlocal counter

        counter += 1

        data = {
            "text": "Target",
            "source_text": (
                "I visited Target in Tucson AZ."
            ),
            "source_type": (
                SourceType.REVIEW
            ),
            "source_id": (
                f"review-{counter}"
            ),
            "resolved_business_id": None,
            "resolution_status": (
                ResolutionStatus.PENDING
            ),
            "confidence_score": None,
        }

        data.update(
            overrides
        )

        mention = Mention(
            **data
        )

        db_session.add(
            mention
        )

        db_session.commit()

        db_session.refresh(
            mention
        )

        return mention

    return create_mention


# ==========================================================
# USER FACTORY
# ==========================================================

@pytest.fixture()
def user_factory(
    db_session,
):

    counter = 0

    def create_user(
        **overrides,
    ):

        nonlocal counter

        counter += 1

        data = {
            "username": (
                f"reviewer-{counter}"
            ),
            # Password is irrelevant for these tests.
            "password_hash": (
                "fake-hashed-password"
            ),
            "role": (
                UserRole.REVIEWER
            ),
        }

        data.update(
            overrides
        )

        user = User(
            **data
        )

        db_session.add(
            user
        )

        db_session.commit()

        db_session.refresh(
            user
        )

        return user

    return create_user


# ==========================================================
# TEMPORARY DOCUMENT STORAGE
# ==========================================================

@pytest.fixture()
def temp_document_storage(
    monkeypatch,
    tmp_path: Path,
):

    data_dir = (
        tmp_path / "data"
    )

    documents_dir = (
        data_dir / "documents"
    )

    # Replace the real project data directory with pytest's
    # temporary folder.
    monkeypatch.setattr(
        DocumentService,
        "PROJECT_ROOT",
        tmp_path,
    )

    monkeypatch.setattr(
        DocumentService,
        "DATA_DIR",
        data_dir,
    )

    monkeypatch.setattr(
        DocumentService,
        "DOCUMENTS_DIR",
        documents_dir,
    )

    return documents_dir