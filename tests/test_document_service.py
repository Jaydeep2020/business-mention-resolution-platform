from pathlib import Path

import pytest

from fastapi import HTTPException
from sqlalchemy import select

from app.models.document import Document
from app.models.resolution_result import (
    ResolutionResult,
)

from app.models.enums import (
    ResolutionDecision,
    ResolutionStatus,
)

from app.services.document_service import (
    DocumentService,
)


# ==========================================================
# SUCCESSFUL RESOLUTION SUMMARY
# ==========================================================

def test_resolution_summary_pdf_is_generated(
    db_session,
    business_factory,
    mention_factory,
    temp_document_storage,
):

    business = business_factory(
        business_id="target-tucson",
        name="Target",
        address="5255 E Broadway Blvd",
        city="Tucson",
        state="AZ",
        is_verified=True,
    )

    mention = mention_factory(
        text="Target",
        source_text=(
            "I visited Target at "
            "5255 E Broadway Blvd "
            "in Tucson AZ."
        ),
        resolved_business_id=business.id,
        resolution_status=(
            ResolutionStatus.AUTO_RESOLVED
        ),
        confidence_score=0.96,
    )

    resolution_result = (
        ResolutionResult(
            mention_id=mention.id,
            business_id=business.id,
            score=0.96,
            decision=(
                ResolutionDecision.AUTO
            ),
            notes=(
                "Automatically resolved because "
                "confidence was above the threshold "
                "and the business is verified."
            ),
        )
    )

    db_session.add(
        resolution_result
    )

    db_session.commit()

    document = (
        DocumentService
        .generate_resolution_summary(
            session=db_session,
            mention_id=mention.id,
        )
    )

    assert document.id is not None

    assert (
        document.type
        == "summary"
    )

    assert (
        document.month
        is None
    )

    assert (
        document.file_path.startswith(
            "data/documents/"
        )
    )

    file_path = (
        DocumentService
        .get_document_path(
            document
        )
    )

    assert file_path.exists()

    assert file_path.is_file()

    assert (
        file_path.suffix
        == ".pdf"
    )

    # Real PDF files begin with %PDF.
    with open(
        file_path,
        "rb",
    ) as pdf_file:

        header = pdf_file.read(
            4
        )

    assert header == b"%PDF"

    stored_document = (
        db_session.execute(
            select(Document)
            .where(
                Document.id
                == document.id
            )
        )
        .scalar_one()
    )

    assert (
        stored_document.file_path
        == document.file_path
    )


# ==========================================================
# PENDING MENTION
# ==========================================================

def test_pending_mention_cannot_generate_summary(
    db_session,
    mention_factory,
    temp_document_storage,
):

    mention = mention_factory(
        resolution_status=(
            ResolutionStatus.PENDING
        )
    )

    with pytest.raises(
        HTTPException
    ) as exception:

        (
            DocumentService
            .generate_resolution_summary(
                session=db_session,
                mention_id=mention.id,
            )
        )

    assert (
        exception.value.status_code
        == 409
    )


# ==========================================================
# DOCUMENT PATH
# ==========================================================

def test_get_document_path_returns_existing_file(
    db_session,
    temp_document_storage,
):

    temp_document_storage.mkdir(
        parents=True,
        exist_ok=True,
    )

    test_file = (
        temp_document_storage
        / "test.pdf"
    )

    test_file.write_bytes(
        b"%PDF-test-file"
    )

    relative_path = (
        "data/documents/test.pdf"
    )

    from datetime import datetime

    document = Document(
        type="summary",
        file_path=relative_path,
        generated_at=datetime.now(),
        month=None,
    )

    db_session.add(
        document
    )

    db_session.commit()

    result = (
        DocumentService
        .get_document_path(
            document
        )
    )

    assert (
        result.resolve()
        == test_file.resolve()
    )