from datetime import datetime

from fastapi import (
    HTTPException,
    status,
)

from sqlalchemy import (
    func,
    select,
)

from sqlalchemy.orm import Session

from app.models.mention import Mention

from app.models.resolution_result import (
    ResolutionResult,
)

from app.models.enums import (
    ResolutionStatus,
)


class ReportingService:

    # ======================================================
    # MONTH RANGE
    # ======================================================

    @staticmethod
    def get_month_range(
        month: str,
    ) -> tuple[
        datetime,
        datetime,
    ]:

        try:

            start = datetime.strptime(
                month,
                "%Y-%m",
            )

        except ValueError:

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
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
    # MONTHLY DATA
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

        # ==================================================
        # PROCESSED
        # ==================================================

        mentions_processed = (
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
                    != ResolutionStatus.PENDING,
                )
            )
            .scalar_one()
        )

        # ==================================================
        # AUTO
        # ==================================================

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

        # ==================================================
        # APPROVED
        # ==================================================

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

        # ==================================================
        # REJECTED
        # ==================================================

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

        # ==================================================
        # SENT FOR REVIEW
        #
        # Do NOT check current decision == REVIEW,
        # because that decision can later become APPROVED
        # or REJECTED.
        # ==================================================

        sent_for_review = (
            session.execute(
                select(
                    func.count(
                        func.distinct(
                            ResolutionResult
                            .mention_id
                        )
                    )
                )
                .where(
                    ResolutionResult.created_at
                    >= start_date,

                    ResolutionResult.created_at
                    < end_date,

                    ResolutionResult.notes.ilike(
                        "Sent for review because%"
                    ),
                )
            )
            .scalar_one()
        )

        # ==================================================
        # MATCH RATE
        # ==================================================

        successful_matches = (
            auto_resolved
            + reviewer_approved
        )

        if mentions_processed:

            match_rate = (
                successful_matches
                / mentions_processed
                * 100
            )

        else:

            match_rate = 0.0

        match_rate = round(
            match_rate,
            2,
        )

        # ==================================================
        # REVIEW REASONS
        # ==================================================

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

        review_reasons = [
            {
                "reason": reason,
                "count": count,
            }
            for reason, count
            in review_reason_rows
        ]

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

            "rejected": (
                rejected
            ),

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