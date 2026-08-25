from fastapi import (
    HTTPException,
    status,
)

from sqlalchemy import select

from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.mention import Mention
from app.models.resolution_result import (
    ResolutionResult,
)
from app.models.user import User

from app.models.enums import (
    ResolutionDecision,
    ResolutionStatus,
)


class ResolutionSnapshotService:

    @staticmethod
    def get_resolution_snapshot(
        session: Session,
        mention_id: int,
    ) -> dict:

        # ==================================================
        # MENTION
        # ==================================================

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
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Mention not found",
            )

        successful_statuses = {
            ResolutionStatus.AUTO_RESOLVED,
            ResolutionStatus.APPROVED,
        }

        if (
            mention.resolution_status
            not in successful_statuses
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Mention has not been "
                    "successfully resolved."
                ),
            )

        # ==================================================
        # SELECTED BUSINESS
        # ==================================================

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

        # ==================================================
        # RESULTS
        # ==================================================

        results = list(
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

        approved_result = None

        for result in results:

            if (
                result.decision
                == ResolutionDecision.APPROVED
            ):

                approved_result = result

                break

        # ==================================================
        # REVIEWER
        # ==================================================

        reviewer_username = None

        if (
            approved_result
            and approved_result.reviewer_id
        ):

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

                reviewer_username = (
                    reviewer.username
                )

        # ==================================================
        # CANDIDATES
        # ==================================================

        candidates = []

        for result in results:

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

        # ==================================================
        # MAIN RESULT
        # ==================================================

        main_result = None

        if approved_result:

            main_result = (
                approved_result
            )

        else:

            for result in results:

                if (
                    result.business_id
                    == mention.resolved_business_id
                ):

                    main_result = (
                        result
                    )

                    break

        # ==================================================
        # RESPONSE
        # ==================================================

        resolved_business_data = None

        if selected_business:

            resolved_business_data = {
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

        return {
            "mention_id": mention.id,

            "mention_text": (
                mention.text
            ),

            "source_type": (
                mention.source_type.value
                if mention.source_type
                else None
            ),

            "source_id": (
                mention.source_id
            ),

            "source_text": (
                mention.source_text
            ),

            "resolution_status": (
                mention
                .resolution_status
                .value
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

            "decision_notes": (
                main_result.notes
                if main_result
                else None
            ),

            "resolved_business": (
                resolved_business_data
            ),

            "candidates": (
                candidates
            ),
        }