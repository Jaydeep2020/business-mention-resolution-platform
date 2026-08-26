from datetime import datetime

import pytest

from fastapi import HTTPException
from sqlalchemy import select

from app.models.document import Document
from app.models.mention import Mention
from app.models.resolution_result import (
    ResolutionResult,
)

from app.models.enums import (
    ResolutionDecision,
    ResolutionStatus,
    SourceType,
)

from app.services.document_service import (
    DocumentService,
)


REPORT_DATE = datetime(
    2026,
    8,
    15,
    12,
    0,
    0,
)


# ==========================================================
# HELPER
# ==========================================================

def create_monthly_mention(
    session,
    number: int,
    resolution_status: ResolutionStatus,
    processed_at: datetime = REPORT_DATE,
):

    mention = Mention(
        text=f"Business {number}",
        source_text=(
            f"I visited Business {number}."
        ),
        source_type=SourceType.REVIEW,
        source_id=f"monthly-review-{number}",
        resolution_status=resolution_status,
        confidence_score=0.90,
        created_at=processed_at,
        updated_at=processed_at,
    )

    session.add(
        mention
    )

    session.flush()

    return mention


# ==========================================================
# REPORT STATISTICS
# ==========================================================

def test_monthly_report_statistics(
    db_session,
    business_factory,
):

    business = business_factory(
        business_id="monthly-business",
        name="Monthly Business",
    )

    mentions = []

    # ------------------------------------------------------
    # 6 automatically resolved
    # ------------------------------------------------------

    for i in range(1, 7):

        mention = (
            create_monthly_mention(
                session=db_session,
                number=i,
                resolution_status=(
                    ResolutionStatus.AUTO_RESOLVED
                ),
            )
        )

        mention.resolved_business_id = (
            business.id
        )

        mentions.append(
            mention
        )

    # ------------------------------------------------------
    # 2 approved by reviewers
    # ------------------------------------------------------

    for i in range(7, 9):

        mention = (
            create_monthly_mention(
                session=db_session,
                number=i,
                resolution_status=(
                    ResolutionStatus.APPROVED
                ),
            )
        )

        mention.resolved_business_id = (
            business.id
        )

        mentions.append(
            mention
        )

    # ------------------------------------------------------
    # 1 rejected
    # ------------------------------------------------------

    rejected_mention = (
        create_monthly_mention(
            session=db_session,
            number=9,
            resolution_status=(
                ResolutionStatus.REJECTED
            ),
        )
    )

    mentions.append(
        rejected_mention
    )

    # ------------------------------------------------------
    # 1 still waiting for review
    # ------------------------------------------------------

    review_mention = (
        create_monthly_mention(
            session=db_session,
            number=10,
            resolution_status=(
                ResolutionStatus.SENT_FOR_REVIEWER
            ),
        )
    )

    mentions.append(
        review_mention
    )

    db_session.flush()

    # ------------------------------------------------------
    # Historical review reasons
    #
    # 4 mentions went through review:
    #
    # two approved
    # one rejected
    # one still in review
    # ------------------------------------------------------

    review_results = [
        ResolutionResult(
            mention_id=mentions[6].id,
            business_id=business.id,
            score=0.80,
            decision=ResolutionDecision.REVIEW,
            notes=(
                "Sent for review because multiple "
                "candidate businesses have similar "
                "confidence scores."
            ),
            created_at=REPORT_DATE,
            updated_at=REPORT_DATE,
        ),
        ResolutionResult(
            mention_id=mentions[7].id,
            business_id=business.id,
            score=0.79,
            decision=ResolutionDecision.REVIEW,
            notes=(
                "Sent for review because multiple "
                "candidate businesses have similar "
                "confidence scores."
            ),
            created_at=REPORT_DATE,
            updated_at=REPORT_DATE,
        ),
        ResolutionResult(
            mention_id=mentions[8].id,
            business_id=business.id,
            score=0.74,
            decision=ResolutionDecision.REVIEW,
            notes=(
                "Sent for review because confidence "
                "did not reach the automatic "
                "resolution threshold."
            ),
            created_at=REPORT_DATE,
            updated_at=REPORT_DATE,
        ),
        ResolutionResult(
            mention_id=mentions[9].id,
            business_id=business.id,
            score=0.96,
            decision=ResolutionDecision.REVIEW,
            notes=(
                "Sent for review because the "
                "matched business is unverified."
            ),
            created_at=REPORT_DATE,
            updated_at=REPORT_DATE,
        ),
    ]

    db_session.add_all(
        review_results
    )

    # ------------------------------------------------------
    # Add records that must NOT be counted.
    # ------------------------------------------------------

    create_monthly_mention(
        session=db_session,
        number=11,
        resolution_status=(
            ResolutionStatus.AUTO_RESOLVED
        ),
        processed_at=datetime(
            2026,
            7,
            15,
        ),
    )

    create_monthly_mention(
        session=db_session,
        number=12,
        resolution_status=(
            ResolutionStatus.PENDING
        ),
        processed_at=REPORT_DATE,
    )

    db_session.commit()

    report = (
        DocumentService
        .get_monthly_report_data(
            session=db_session,
            month="2026-08",
        )
    )

    assert (
        report["month"]
        == "2026-08"
    )

    assert (
        report["mentions_processed"]
        == 10
    )

    assert (
        report["auto_resolved"]
        == 6
    )

    assert (
        report["reviewer_approved"]
        == 2
    )

    assert (
        report["rejected"]
        == 1
    )

    assert (
        report["sent_for_review"]
        == 4
    )

    # Successful:
    #
    # 6 auto + 2 approved = 8
    #
    # 8 / 10 * 100 = 80%
    assert (
        report["match_rate"]
        == 80.0
    )

    assert len(
        report["review_reasons"]
    ) == 3

    assert (
        report[
            "review_reasons"
        ][0]["count"]
        == 2
    )


# ==========================================================
# PDF GENERATION
# ==========================================================

def test_monthly_report_pdf_is_generated(
    db_session,
    temp_document_storage,
):

    mention = Mention(
        text="Target",
        source_text=(
            "I visited Target."
        ),
        source_type=SourceType.REVIEW,
        source_id="report-test-1",
        resolution_status=(
            ResolutionStatus.AUTO_RESOLVED
        ),
        confidence_score=0.95,
        created_at=REPORT_DATE,
        updated_at=REPORT_DATE,
    )

    db_session.add(
        mention
    )

    db_session.commit()

    result = (
        DocumentService
        .generate_monthly_report(
            session=db_session,
            month="2026-08",
        )
    )

    document = (
        result["document"]
    )

    report = (
        result["report"]
    )

    assert (
        document.type
        == "monthly_report"
    )

    assert (
        document.month
        == "2026-08"
    )

    assert (
        report["mentions_processed"]
        == 1
    )

    assert (
        report["auto_resolved"]
        == 1
    )

    assert (
        report["match_rate"]
        == 100.0
    )

    file_path = (
        DocumentService
        .get_document_path(
            document
        )
    )

    assert file_path.exists()

    assert (
        file_path.suffix
        == ".pdf"
    )

    with open(
        file_path,
        "rb",
    ) as pdf_file:

        assert (
            pdf_file.read(4)
            == b"%PDF"
        )


# ==========================================================
# DUPLICATE MONTHLY REPORT
# ==========================================================

def test_existing_monthly_report_is_reused(
    db_session,
    temp_document_storage,
):

    mention = Mention(
        text="Target",
        source_text="Target visit",
        source_type=SourceType.REVIEW,
        source_id="duplicate-report-test",
        resolution_status=(
            ResolutionStatus.AUTO_RESOLVED
        ),
        confidence_score=0.95,
        created_at=REPORT_DATE,
        updated_at=REPORT_DATE,
    )

    db_session.add(
        mention
    )

    db_session.commit()

    first_result = (
        DocumentService
        .generate_monthly_report(
            session=db_session,
            month="2026-08",
        )
    )

    second_result = (
        DocumentService
        .generate_monthly_report(
            session=db_session,
            month="2026-08",
        )
    )

    assert (
        first_result[
            "document"
        ].id
        == second_result[
            "document"
        ].id
    )

    documents = list(
        db_session.execute(
            select(Document)
            .where(
                Document.type
                == "monthly_report",
                Document.month
                == "2026-08",
            )
        )
        .scalars()
        .all()
    )

    assert len(
        documents
    ) == 1


# ==========================================================
# INVALID MONTH
# ==========================================================

def test_invalid_month_is_rejected(
    db_session,
):

    with pytest.raises(
        HTTPException
    ) as exception:

        (
            DocumentService
            .get_monthly_report_data(
                session=db_session,
                month="August-2026",
            )
        )

    assert (
        exception.value.status_code
        == 400
    )