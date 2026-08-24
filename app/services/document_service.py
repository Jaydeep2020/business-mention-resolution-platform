# It:
#
# fetches the resolution
# fetches the mention
# fetches the selected business
# fetches all candidates
# creates the PDF
# saves it inside data/documents/
# creates a Document database record

from datetime import datetime, timezone
from math import ceil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.documents.resolution_summary import (
    generate_resolution_summary_pdf,
)

from app.documents.monthly_report import (
    generate_monthly_report_pdf,
)

from app.models.user import User
from app.models.business import Business
from app.models.document import Document
from app.models.mention import Mention
from app.models.resolution_result import (
    ResolutionResult,
)

from app.models.enums import (
    ResolutionDecision,
    ResolutionStatus,
)


class DocumentService:

    # ------------------------------------------------------
    # DATA DIRECTORY
    # ------------------------------------------------------

    PROJECT_ROOT = (
        Path(__file__)
        .resolve()
        .parents[2]
    )

    DATA_DIR = PROJECT_ROOT / "data"

    DOCUMENTS_DIR = (
        DATA_DIR / "documents"
    )

    # ------------------------------------------------------
    # GENERATE RESOLUTION SUMMARY
    # ------------------------------------------------------

    @classmethod
    def generate_resolution_summary(
        cls,
        session: Session,
        mention_id: int,
    ) -> Document:

        # --------------------------------------------------
        # Get mention
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Summary should only be generated after a
        # successful resolution.
        # --------------------------------------------------

        successful_statuses = {
            ResolutionStatus.AUTO_RESOLVED,
            ResolutionStatus.APPROVED,
        }

        if (
            mention.resolution_status
            not in successful_statuses
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Resolution summary can only be "
                    "generated for a successfully "
                    "resolved mention."
                ),
            )

        # --------------------------------------------------
        # Selected business
        # --------------------------------------------------

        selected_business = None

        if mention.resolved_business_id:

            selected_business = (
                session.execute(
                    select(Business)
                    .where(
                        Business.id
                        == mention.resolved_business_id
                    )
                )
                .scalar_one_or_none()
            )

        # --------------------------------------------------
        # Get resolution results
        # --------------------------------------------------

        resolution_results = list(
            session.execute(
                select(
                    ResolutionResult
                )
                .where(
                    ResolutionResult.mention_id
                    == mention.id
                )
                .order_by(
                    ResolutionResult.score.desc()
                )
            )
            .scalars()
            .all()
        )

        # --------------------------------------------------
        # Reviewer
        # --------------------------------------------------

        reviewer_username = None

        approved_result = None

        for result in resolution_results:

            if (
                result.decision
                == ResolutionDecision.APPROVED
            ):
                approved_result = result
                break

        reviewer = None

        if approved_result and approved_result.reviewer_id:

            reviewer = (
                session.execute(
                    select(User)
                    .where(
                        User.id
                        == approved_result.reviewer_id
                    )
                )
                .scalar_one_or_none()
            )

            if reviewer:
                reviewer_username = reviewer.username

            if reviewer:
                reviewer_username = (
                    reviewer.username
                )

        # --------------------------------------------------
        # Build candidate data
        # --------------------------------------------------

        candidates = []

        for result in resolution_results:

            business = (
                session.execute(
                    select(Business)
                    .where(
                        Business.id
                        == result.business_id
                    )
                )
                .scalar_one_or_none()
            )

            if business is None:
                continue

            candidates.append(
                {
                    "business_name": (
                        business.name
                    ),
                    "city": (
                        business.city
                    ),
                    "score": (
                        result.score
                    ),
                    "is_verified": (
                        business.is_verified
                    ),
                    "decision": (
                        result.decision.value
                    ),
                }
            )

        # --------------------------------------------------
        # Main decision
        # --------------------------------------------------

        main_result = None

        if approved_result:

            main_result = approved_result

        else:

            for result in resolution_results:

                if (
                    result.business_id
                    == mention.resolved_business_id
                ):
                    main_result = result
                    break

        decision_notes = None

        if main_result:
            decision_notes = (
                main_result.notes
            )

        # --------------------------------------------------
        # Prepare PDF data
        # --------------------------------------------------

        pdf_data = {
            "mention_id": mention.id,
            "mention_text": mention.text,
            "source_type": (
                mention.source_type.value
                if mention.source_type
                else None
            ),
            "source_id": mention.source_id,
            "source_text": mention.source_text,
            "resolution_status": (
                mention.resolution_status.value
            ),
            "decision": (
                main_result.decision.value
                if main_result
                else None
            ),
            "confidence_score": (
                mention.confidence_score
            ),
            "resolved_business_id": (
                mention.resolved_business_id
            ),
            "reviewer_username": (
                reviewer_username
            ),
            "reviewer_notes": (
                approved_result.notes
                if approved_result
                else None
            ),
            "decision_notes": decision_notes,
            "resolved_business": None,
            "candidates": candidates,
        }

        if selected_business:

            pdf_data[
                "resolved_business"
            ] = {
                "business_id": (
                    selected_business.business_id
                ),
                "name": (
                    selected_business.name
                ),
                "address": (
                    selected_business.address
                ),
                "city": (
                    selected_business.city
                ),
                "state": (
                    selected_business.state
                ),
                "postal_code": (
                    selected_business.postal_code
                ),
                "is_verified": (
                    selected_business.is_verified
                ),
            }

        # --------------------------------------------------
        # Make directory
        # --------------------------------------------------

        cls.DOCUMENTS_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        # --------------------------------------------------
        # Generate filename
        # --------------------------------------------------

        filename = (
            f"resolution_summary_"
            f"{mention.id}_"
            f"{uuid4().hex[:8]}.pdf"
        )

        absolute_path = (
            cls.DOCUMENTS_DIR
            / filename
        )

        # --------------------------------------------------
        # Generate actual PDF
        # --------------------------------------------------

        generate_resolution_summary_pdf(
            output_path=absolute_path,
            data=pdf_data,
        )

        # Store path relative to project root.
        relative_path = (
            absolute_path
            .relative_to(
                cls.PROJECT_ROOT
            )
            .as_posix()
        )

        # --------------------------------------------------
        # Create Document database row
        # --------------------------------------------------

        document = Document(
            type="summary",
            file_path=relative_path,
            generated_at=datetime.now(
                timezone.utc
            ).replace(tzinfo=None),
            month=None,
        )

        try:

            session.add(document)
            session.commit()
            session.refresh(document)

        except Exception:

            session.rollback()

            # If DB insert fails, remove the generated
            # file so we don't leave an orphan.
            if absolute_path.exists():
                absolute_path.unlink()

            raise

        return document

    # ------------------------------------------------------
    # GET DOCUMENT
    # ------------------------------------------------------

    @staticmethod
    def get_document(
        session: Session,
        document_id: int,
    ) -> Document:

        document = (
            session.execute(
                select(Document)
                .where(
                    Document.id
                    == document_id
                )
            )
            .scalar_one_or_none()
        )

        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        return document

    # ------------------------------------------------------
    # LIST DOCUMENTS
    # ------------------------------------------------------

    @staticmethod
    def get_documents(
        session: Session,
        page: int = 1,
        page_size: int = 20,
        document_type: str | None = None,
    ):

        if page < 1:
            page = 1

        if page_size < 1:
            page_size = 20

        if page_size > 100:
            page_size = 100

        conditions = []

        if document_type:

            conditions.append(
                Document.type
                == document_type
            )

        count_stmt = select(
            func.count(Document.id)
        )

        if conditions:
            count_stmt = (
                count_stmt.where(
                    *conditions
                )
            )

        total = (
            session.execute(
                count_stmt
            )
            .scalar_one()
        )

        stmt = select(Document)

        if conditions:
            stmt = stmt.where(
                *conditions
            )

        stmt = (
            stmt
            .order_by(
                Document.generated_at.desc()
            )
            .offset(
                (page - 1) * page_size
            )
            .limit(page_size)
        )

        documents = list(
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
            "items": documents,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }

    # ------------------------------------------------------
    # GET FILE PATH
    # ------------------------------------------------------

    @classmethod
    def get_document_path(
        cls,
        document: Document,
    ) -> Path:

        path = (
            cls.PROJECT_ROOT
            / document.file_path
        )

        # Security check:
        # Prevent a malicious DB path from escaping
        # the project directory.
        try:

            path.resolve().relative_to(
                cls.PROJECT_ROOT.resolve()
            )

        except ValueError:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document path",
            )

        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found",
            )

        if not path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found",
            )

        return path


    # ======================================================
    # MONTHLY REPORT HELPERS
    # ======================================================

    @staticmethod
    def get_month_range(
        month: str,
    ) -> tuple[datetime, datetime]:
        """
        Convert:

        2026-08

        into:

        start = 2026-08-01
        end   = 2026-09-01
        """

        try:

            start = datetime.strptime(
                month,
                "%Y-%m",
            )

        except ValueError:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Month must be in "
                    "YYYY-MM format."
                ),
            )

        if start.month == 12:

            end = datetime(
                start.year + 1,
                1,
                1,
            )

        else:

            end = datetime(
                start.year,
                start.month + 1,
                1,
            )

        return start, end


    # ======================================================
    # GET MONTHLY REPORT DATA
    # ======================================================

    @classmethod
    def get_monthly_report_data(
        cls,
        session: Session,
        month: str,
    ) -> dict:

        start_date, end_date = (
            cls.get_month_range(
                month
            )
        )

        # --------------------------------------------------
        # Mentions processed
        #
        # Since your current Mention table has no
        # resolved_at column, updated_at is used to
        # determine when the mention was processed.
        # --------------------------------------------------

        processed_conditions = [
            Mention.updated_at >= start_date,
            Mention.updated_at < end_date,
            Mention.resolution_status
            != ResolutionStatus.PENDING,
        ]

        mentions_processed = (
            session.execute(
                select(
                    func.count(
                        Mention.id
                    )
                )
                .where(
                    *processed_conditions
                )
            )
            .scalar_one()
        )

        # --------------------------------------------------
        # Automatically resolved
        # --------------------------------------------------

        auto_resolved = (
            session.execute(
                select(
                    func.count(
                        Mention.id
                    )
                )
                .where(
                    Mention.updated_at
                    >= start_date,
                    Mention.updated_at
                    < end_date,
                    Mention.resolution_status
                    == ResolutionStatus.AUTO_RESOLVED,
                )
            )
            .scalar_one()
        )

        # --------------------------------------------------
        # Reviewer approved
        # --------------------------------------------------

        reviewer_approved = (
            session.execute(
                select(
                    func.count(
                        Mention.id
                    )
                )
                .where(
                    Mention.updated_at
                    >= start_date,
                    Mention.updated_at
                    < end_date,
                    Mention.resolution_status
                    == ResolutionStatus.APPROVED,
                )
            )
            .scalar_one()
        )

        # --------------------------------------------------
        # Rejected mentions
        # --------------------------------------------------

        rejected = (
            session.execute(
                select(
                    func.count(
                        Mention.id
                    )
                )
                .where(
                    Mention.updated_at
                    >= start_date,
                    Mention.updated_at
                    < end_date,
                    Mention.resolution_status
                    == ResolutionStatus.REJECTED,
                )
            )
            .scalar_one()
        )

        # --------------------------------------------------
        # Sent for review
        #
        # Important:
        # A mention may later become APPROVED or REJECTED.
        # Therefore we should not count only mentions whose
        # current status is SENT_FOR_REVIEWER.
        #
        # ResolutionResult stores the original review
        # decision, so we count distinct mentions that
        # received the main "Sent for review..." result.
        # --------------------------------------------------

        sent_for_review = (
            session.execute(
                select(
                    func.count(
                        func.distinct(
                            ResolutionResult.mention_id
                        )
                    )
                )
                .where(
                    ResolutionResult.created_at
                    >= start_date,
                    ResolutionResult.created_at
                    < end_date,
                    ResolutionResult.decision
                    == ResolutionDecision.REVIEW,
                    ResolutionResult.notes.ilike(
                        "Sent for review because%"
                    ),
                )
            )
            .scalar_one()
        )

        # --------------------------------------------------
        # Match rate
        # --------------------------------------------------

        successful_matches = (
            auto_resolved
            + reviewer_approved
        )

        if mentions_processed > 0:

            match_rate = (
                successful_matches
                / mentions_processed
            ) * 100

        else:

            match_rate = 0.0

        match_rate = round(
            match_rate,
            2,
        )

        # --------------------------------------------------
        # Most common review reasons
        # --------------------------------------------------

        review_reason_rows = (
            session.execute(
                select(
                    ResolutionResult.notes,
                    func.count(
                        ResolutionResult.id
                    ).label(
                        "reason_count"
                    ),
                )
                .where(
                    ResolutionResult.created_at
                    >= start_date,
                    ResolutionResult.created_at
                    < end_date,
                    ResolutionResult.decision
                    == ResolutionDecision.REVIEW,
                    ResolutionResult.notes.is_not(
                        None
                    ),
                    ResolutionResult.notes.ilike(
                        "Sent for review because%"
                    ),
                )
                .group_by(
                    ResolutionResult.notes
                )
                .order_by(
                    func.count(
                        ResolutionResult.id
                    ).desc()
                )
                .limit(10)
            )
            .all()
        )

        review_reasons = []

        for (
            reason,
            count,
        ) in review_reason_rows:

            review_reasons.append(
                {
                    "reason": reason,
                    "count": count,
                }
            )

        return {
            "month": month,
            "mentions_processed": (
                mentions_processed
            ),
            "auto_resolved": (
                auto_resolved
            ),
            "reviewer_approved": (
                reviewer_approved
            ),
            "rejected": rejected,
            "sent_for_review": (
                sent_for_review
            ),
            "match_rate": (
                match_rate
            ),
            "review_reasons": (
                review_reasons
            ),
        }


    # ======================================================
    # GENERATE MONTHLY REPORT
    # ======================================================

    @classmethod
    def generate_monthly_report(
        cls,
        session: Session,
        month: str,
    ) -> dict:

        # --------------------------------------------------
        # Validate month first
        # --------------------------------------------------

        cls.get_month_range(
            month
        )

        # --------------------------------------------------
        # Avoid creating the same monthly report multiple
        # times.
        # --------------------------------------------------

        existing_document = (
            session.execute(
                select(Document)
                .where(
                    Document.type
                    == "monthly_report",
                    Document.month
                    == month,
                )
                .order_by(
                    Document.generated_at.desc()
                )
            )
            .scalars()
            .first()
        )

        if existing_document:

            existing_path = (
                cls.PROJECT_ROOT
                / existing_document.file_path
            )

            if (
                existing_path.exists()
                and existing_path.is_file()
            ):

                report_data = (
                    cls.get_monthly_report_data(
                        session=session,
                        month=month,
                    )
                )

                return {
                    "document": (
                        existing_document
                    ),
                    "report": (
                        report_data
                    ),
                }

        # --------------------------------------------------
        # Calculate report statistics
        # --------------------------------------------------

        report_data = (
            cls.get_monthly_report_data(
                session=session,
                month=month,
            )
        )

        # --------------------------------------------------
        # Create output directory
        # --------------------------------------------------

        cls.DOCUMENTS_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        # --------------------------------------------------
        # Filename
        # --------------------------------------------------

        filename = (
            f"monthly_report_"
            f"{month}_"
            f"{uuid4().hex[:8]}"
            f".pdf"
        )

        absolute_path = (
            cls.DOCUMENTS_DIR
            / filename
        )

        # --------------------------------------------------
        # Generate PDF
        # --------------------------------------------------

        generate_monthly_report_pdf(
            output_path=absolute_path,
            data=report_data,
        )

        relative_path = (
            absolute_path
            .relative_to(
                cls.PROJECT_ROOT
            )
            .as_posix()
        )

        # --------------------------------------------------
        # Save document metadata
        # --------------------------------------------------

        document = Document(
            type="monthly_report",
            file_path=relative_path,
            generated_at=datetime.now(
                timezone.utc
            ).replace(
                tzinfo=None
            ),
            month=month,
        )

        try:

            session.add(
                document
            )

            session.commit()

            session.refresh(
                document
            )

        except Exception:

            session.rollback()

            # Remove PDF if DB storage failed.
            if absolute_path.exists():

                absolute_path.unlink()

            raise

        return {
            "document": document,
            "report": report_data,
        }