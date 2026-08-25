from datetime import (
    datetime,
    timezone,
)

from math import ceil

from pathlib import Path

from uuid import uuid4

from fastapi import (
    HTTPException,
    status,
)

from sqlalchemy import (
    func,
    select,
)

from sqlalchemy.orm import Session

from document_service.clients.catalog_client import (
    CatalogClient,
)

from document_service.core.config import (
    settings,
)

from document_service.documents.resolution_summary import (
    generate_resolution_summary_pdf,
)

from document_service.documents.monthly_report import (
    generate_monthly_report_pdf,
)

from document_service.models.document import (
    Document,
)


class DocumentService:

    PROJECT_ROOT = (
        Path(__file__)
        .resolve()
        .parents[2]
    )

    DOCUMENTS_DIR = (
        PROJECT_ROOT
        / settings.DOCUMENTS_DIR
    )

    @staticmethod
    def get_existing_resolution_summary(
            session: Session,
            mention_id: int,
    ) -> Document | None:

        filename_pattern = (
            f"%resolution_summary_{mention_id}_%.pdf"
        )

        return (
            session.execute(
                select(Document)
                .where(
                    Document.type == "summary",
                    Document.file_path.ilike(
                        filename_pattern
                    ),
                )
                .order_by(
                    Document.generated_at.desc()
                )
            )
            .scalars()
            .first()
        )

    # ======================================================
    # RESOLUTION SUMMARY
    # ======================================================

    # @classmethod
    # def generate_resolution_summary(
    #     cls,
    #     session: Session,
    #     mention_id: int,
    # ) -> Document:
    #
    #     existing = (
    #         cls.get_existing_resolution_summary(
    #             session=session,
    #             mention_id=mention_id,
    #         )
    #     )
    #
    #     if existing:
    #
    #         try:
    #
    #             existing_path = (
    #                 cls.get_document_path(
    #                     existing
    #                 )
    #             )
    #
    #             if existing_path.exists():
    #
    #                 return existing
    #
    #         except HTTPException:
    #
    #             # DB row exists but file disappeared.
    #             # Regenerate below.
    #             pass
    #
    #     # ==================================================
    #     # FETCH DATA FROM CATALOG SERVICE
    #     # ==================================================
    #
    #     snapshot = (
    #         CatalogClient
    #         .get_resolution_snapshot(
    #             mention_id=mention_id
    #         )
    #     )
    #
    #     cls.DOCUMENTS_DIR.mkdir(
    #         parents=True,
    #         exist_ok=True,
    #     )
    #
    #     filename = (
    #         f"resolution_summary_"
    #         f"{mention_id}_"
    #         f"{uuid4().hex[:8]}"
    #         f".pdf"
    #     )
    #
    #     absolute_path = (
    #         cls.DOCUMENTS_DIR
    #         / filename
    #     )
    #
    #     # ==================================================
    #     # GENERATE PDF
    #     # ==================================================
    #
    #     generate_resolution_summary_pdf(
    #         output_path=absolute_path,
    #         data=snapshot,
    #     )
    #
    #     relative_path = (
    #         absolute_path
    #         .relative_to(
    #             cls.SERVICE_ROOT
    #         )
    #         .as_posix()
    #     )
    #
    #     now = datetime.now(
    #         timezone.utc
    #     ).replace(
    #         tzinfo=None
    #     )
    #
    #     if existing:
    #
    #         document = existing
    #
    #         document.file_path = (
    #             relative_path
    #         )
    #
    #         document.generated_at = (
    #             now
    #         )
    #
    #     else:
    #
    #         document = Document(
    #             type="summary",
    #             source_reference=(
    #                 source_reference
    #             ),
    #             file_path=relative_path,
    #             generated_at=now,
    #             month=None,
    #         )
    #
    #         session.add(
    #             document
    #         )
    #
    #     try:
    #
    #         session.commit()
    #
    #         session.refresh(
    #             document
    #         )
    #
    #     except Exception:
    #
    #         session.rollback()
    #
    #         if absolute_path.exists():
    #
    #             absolute_path.unlink()
    #
    #         raise
    #
    #     return document

    @classmethod
    def generate_resolution_summary(
            cls,
            session: Session,
            mention_id: int,
    ) -> Document:

        existing = (
            cls.get_existing_resolution_summary(
                session=session,
                mention_id=mention_id,
            )
        )

        if existing:

            try:

                path = cls.get_document_path(
                    existing
                )

                if path.exists():
                    return existing

            except HTTPException:

                # DB record exists but PDF disappeared.
                # Generate a new one below.
                pass

        snapshot = (
            CatalogClient
            .get_resolution_snapshot(
                mention_id=mention_id
            )
        )

        cls.DOCUMENTS_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        filename = (
            f"resolution_summary_"
            f"{mention_id}_"
            f"{uuid4().hex[:8]}"
            f".pdf"
        )

        absolute_path = (
                cls.DOCUMENTS_DIR
                / filename
        )

        generate_resolution_summary_pdf(
            output_path=absolute_path,
            data=snapshot,
        )

        relative_path = (
            absolute_path
            .relative_to(
                cls.SERVICE_ROOT
            )
            .as_posix()
        )

        document = Document(
            type="summary",
            file_path=relative_path,
            generated_at=(
                datetime.now(
                    timezone.utc
                )
                .replace(
                    tzinfo=None
                )
            ),
            month=None,
        )

        try:

            session.add(document)

            session.commit()

            session.refresh(document)

        except Exception:

            session.rollback()

            if absolute_path.exists():
                absolute_path.unlink()

            raise

        return document


    # ======================================================
    # GET
    # ======================================================

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
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Document not found"
                ),
            )

        return document


    # ======================================================
    # LIST
    # ======================================================

    @staticmethod
    def get_documents(
        session: Session,
        page: int = 1,
        page_size: int = 20,
        document_type: str | None = None,
    ) -> dict:

        conditions = []

        if document_type:

            conditions.append(
                Document.type
                == document_type
            )

        count_stmt = select(
            func.count(
                Document.id
            )
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

        stmt = select(
            Document
        )

        if conditions:

            stmt = stmt.where(
                *conditions
            )

        stmt = (
            stmt
            .order_by(
                Document
                .generated_at
                .desc()
            )
            .offset(
                (page - 1)
                * page_size
            )
            .limit(
                page_size
            )
        )

        items = list(
            session.execute(
                stmt
            )
            .scalars()
            .all()
        )

        total_pages = (
            ceil(
                total / page_size
            )
            if total
            else 0
        )

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (
                total_pages
            ),
        }


    # ======================================================
    # FILE PATH
    # ======================================================

    @classmethod
    def get_document_path(
            cls,
            document: Document,
    ) -> Path:

        path = (
                cls.PROJECT_ROOT
                / document.file_path
        )

        # ======================================================
        # SECURITY CHECK
        # ======================================================

        try:

            path.resolve().relative_to(
                cls.DOCUMENTS_DIR.resolve()
            )

        except ValueError:

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "Invalid document path"
                ),
            )

        # ======================================================
        # FILE EXISTS
        # ======================================================

        if (
                not path.exists()
                or not path.is_file()
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Document file not found"
                ),
            )

        return path


    # ======================================================
    # MONTHLY REPORT
    # ======================================================

    @classmethod
    def generate_monthly_report(
        cls,
        session: Session,
        month: str,
    ) -> dict:

        # Validation happens through Pydantic
        # but this identifier is useful here.
        source_reference = (
            f"month:{month}"
        )

        existing = (
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

        # ==================================================
        # ASK CATALOG SERVICE FOR STATISTICS
        # ==================================================

        report_data = (
            CatalogClient
            .get_monthly_report_data(
                month=month
            )
        )

        if existing:

            try:

                existing_path = (
                    cls.get_document_path(
                        existing
                    )
                )

                if existing_path.exists():

                    return {
                        "document": (
                            existing
                        ),
                        "report": (
                            report_data
                        ),
                    }

            except HTTPException:

                pass

        cls.DOCUMENTS_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

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

        now = datetime.now(
            timezone.utc
        ).replace(
            tzinfo=None
        )

        if existing:

            document = existing

            document.file_path = (
                relative_path
            )

            document.generated_at = (
                now
            )

            document.month = (
                month
            )

        else:

            document = Document(
                type=(
                    "monthly_report"
                ),
                source_reference=(
                    source_reference
                ),
                file_path=(
                    relative_path
                ),
                generated_at=now,
                month=month,
            )

            session.add(
                document
            )

        try:

            session.commit()

            session.refresh(
                document
            )

        except Exception:

            session.rollback()

            if absolute_path.exists():

                absolute_path.unlink()

            raise

        return {
            "document": document,
            "report": report_data,
        }