from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.mention import Mention
from app.models.resolution_result import ResolutionResult

from app.models.enums import (
    ResolutionDecision,
    ResolutionStatus,
)

from app.services.candidate_service import (
    CandidateService,
)

from app.services.document_service import (
    DocumentService,
)


class ResolutionService:

    @staticmethod
    def resolve_mention(
        session: Session,
        mention_id: int,
        max_candidates: int = 5,
    ) -> dict:

        # --------------------------------------------------
        # 1. Get mention
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
        # 2. Make sure mention is pending
        # --------------------------------------------------

        if (
            mention.resolution_status
            != ResolutionStatus.PENDING
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Mention has already gone "
                    "through resolution."
                ),
            )

        # --------------------------------------------------
        # 3. Find candidates
        # --------------------------------------------------

        candidates = (
            CandidateService.get_candidates(
                session=session,
                mention=mention,
                max_candidates=max_candidates,
            )
        )

        if not candidates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "No candidate businesses found "
                    "for this mention."
                ),
            )

        # --------------------------------------------------
        # 4. Remove previous candidate results
        #    just in case resolution is retried.
        # --------------------------------------------------

        previous_results = list(
            session.execute(
                select(ResolutionResult)
                .where(
                    ResolutionResult.mention_id
                    == mention.id
                )
            )
            .scalars()
            .all()
        )

        for result in previous_results:
            session.delete(result)

        # --------------------------------------------------
        # 5. Get best candidate
        # --------------------------------------------------

        best_candidate = candidates[0]

        best_business = (
            best_candidate["business"]
        )

        best_score = (
            best_candidate["score"]
        )

        # --------------------------------------------------
        # 6. Check ambiguity
        # --------------------------------------------------

        ambiguous = False

        if len(candidates) >= 2:

            second_score = (
                candidates[1]["score"]
            )

            score_gap = (
                best_score
                - second_score
            )

            if (
                score_gap
                < CandidateService.AMBIGUITY_GAP
            ):
                ambiguous = True

        # --------------------------------------------------
        # 7. Check verified status
        # --------------------------------------------------

        is_verified = (
            best_business.is_verified
        )

        # --------------------------------------------------
        # 8. Decide result
        # --------------------------------------------------

        can_auto_resolve = (
            best_score
            >= CandidateService.AUTO_RESOLUTION_THRESHOLD
            and not ambiguous
            and is_verified
        )

        if can_auto_resolve:

            mention.resolution_status = (
                ResolutionStatus.AUTO_RESOLVED
            )

            mention.resolved_business_id = (
                best_business.id
            )

            mention.confidence_score = (
                best_score
            )

            best_decision = (
                ResolutionDecision.AUTO
            )

            note = (
                "Automatically resolved because "
                "confidence was above the threshold "
                "and the business is verified."
            )

        else:

            mention.resolution_status = (
                ResolutionStatus.SENT_FOR_REVIEWER
            )

            mention.resolved_business_id = None

            mention.confidence_score = (
                best_score
            )

            best_decision = (
                ResolutionDecision.REVIEW
            )

            if not is_verified:

                note = (
                    "Sent for review because the "
                    "matched business is unverified."
                )

            elif ambiguous:

                note = (
                    "Sent for review because multiple "
                    "candidate businesses have similar "
                    "confidence scores."
                )

            else:

                note = (
                    "Sent for review because confidence "
                    "did not reach the automatic "
                    "resolution threshold."
                )

        # --------------------------------------------------
        # 9. Store all candidate results
        # --------------------------------------------------

        for index, candidate in enumerate(
            candidates
        ):

            business = candidate["business"]

            if index == 0:

                decision = best_decision
                candidate_note = note

            else:

                decision = (
                    ResolutionDecision.REVIEW
                )

                candidate_note = (
                    "Candidate generated during "
                    "automatic resolution."
                )

            result = ResolutionResult(
                mention_id=mention.id,
                business_id=business.id,
                score=candidate["score"],
                decision=decision,
                notes=candidate_note,
            )

            session.add(result)

        try:

            session.flush()

            session.refresh(mention)

            session.commit()

        except Exception:

            session.rollback()
            raise

        # --------------------------------------------------
        # Generate resolution summary for automatically
        # resolved mentions.
        # --------------------------------------------------

        document_id = None

        if (
            mention.resolution_status
            == ResolutionStatus.AUTO_RESOLVED
        ):
            document = (
                DocumentService
                .generate_resolution_summary(
                    session=session,
                    mention_id=mention.id,
                )
            )

            document_id = document.id

        return {
            "mention_id": mention.id,
            "mention_text": mention.text,
            "resolution_status": (
                mention.resolution_status.value
            ),
            "confidence_score": (
                mention.confidence_score
            ),
            "resolved_business_id": (
                mention.resolved_business_id
            ),
            "document_id": document_id,
            "candidates": [
                {
                    "business_id": (
                        candidate["business"].id
                    ),
                    "catalog_business_id": (
                        candidate["business"].business_id
                    ),
                    "business_name": (
                        candidate["business"].name
                    ),
                    "city": (
                        candidate["business"].city
                    ),
                    "state": (
                        candidate["business"].state
                    ),
                    "address": (
                        candidate["business"].address
                    ),
                    "score": (
                        candidate["score"]
                    ),
                    "name_score": (
                        candidate["name_score"]
                    ),
                    "city_score": (
                        candidate["city_score"]
                    ),
                    "state_score": (
                        candidate["state_score"]
                    ),
                    "address_score": (
                        candidate["address_score"]
                    ),
                    "is_verified": (
                        candidate["business"].is_verified
                    ),
                }
                for candidate in candidates
            ],
        }

    # ------------------------------------------------------
    # GET RESOLUTION RESULTS
    # ------------------------------------------------------

    @staticmethod
    def get_resolution_results(
        session: Session,
        page: int = 1,
        page_size: int = 20,
    ):

        if page < 1:
            page = 1

        if page_size < 1:
            page_size = 20

        if page_size > 100:
            page_size = 100

        count_stmt = select(
            func.count(
                ResolutionResult.id
            )
        )

        total = (
            session.execute(count_stmt)
            .scalar_one()
        )

        stmt = (
            select(ResolutionResult)
            .order_by(
                ResolutionResult.id.desc()
            )
            .offset(
                (page - 1) * page_size
            )
            .limit(page_size)
        )

        results = list(
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
            "items": results,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }

    # ------------------------------------------------------
    # REVIEW QUEUE
    # ------------------------------------------------------

    @staticmethod
    def get_review_queue(
        session: Session,
        page: int = 1,
        page_size: int = 20,
    ):

        if page < 1:
            page = 1

        if page_size < 1:
            page_size = 20

        if page_size > 100:
            page_size = 100

        count_stmt = (
            select(
                func.count(
                    ResolutionResult.id
                )
            )
            .join(
                Mention,
                Mention.id
                == ResolutionResult.mention_id,
            )
            .where(
                Mention.resolution_status
                == ResolutionStatus.SENT_FOR_REVIEWER,
                ResolutionResult.decision
                == ResolutionDecision.REVIEW,
            )
        )

        total = (
            session.execute(count_stmt)
            .scalar_one()
        )

        stmt = (
            select(ResolutionResult)
            .join(
                Mention,
                Mention.id
                == ResolutionResult.mention_id,
            )
            .where(
                Mention.resolution_status
                == ResolutionStatus.SENT_FOR_REVIEWER,
                ResolutionResult.decision
                == ResolutionDecision.REVIEW,
            )
            .order_by(
                ResolutionResult.score.desc()
            )
            .offset(
                (page - 1) * page_size
            )
            .limit(page_size)
        )

        results = list(
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
            "items": results,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }

    # ------------------------------------------------------
    # APPROVE
    # ------------------------------------------------------

    @staticmethod
    def approve_resolution(
        session: Session,
        result_id: int,
        reviewer_id: int,
        notes: str | None = None,
    ) -> ResolutionResult:

        result = (
            session.execute(
                select(
                    ResolutionResult
                )
                .where(
                    ResolutionResult.id
                    == result_id
                )
            )
            .scalar_one_or_none()
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resolution result not found",
            )

        mention = (
            session.execute(
                select(Mention)
                .where(
                    Mention.id
                    == result.mention_id
                )
            )
            .scalar_one_or_none()
        )

        if mention is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mention not found",
            )

        if (
            mention.resolution_status
            != ResolutionStatus.SENT_FOR_REVIEWER
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This mention is not currently "
                    "waiting for review."
                ),
            )

        # --------------------------------------------------
        # Reject approving a result that isn't a review
        # candidate.
        # --------------------------------------------------

        if (
            result.decision
            != ResolutionDecision.REVIEW
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Only review candidates can "
                    "be approved."
                ),
            )

        # --------------------------------------------------
        # Set selected result as approved
        # --------------------------------------------------

        result.decision = (
            ResolutionDecision.APPROVED
        )

        result.reviewer_id = reviewer_id
        result.notes = notes

        # --------------------------------------------------
        # Update mention
        # --------------------------------------------------

        mention.resolved_business_id = (
            result.business_id
        )

        mention.confidence_score = (
            result.score
        )

        mention.resolution_status = (
            ResolutionStatus.APPROVED
        )

        # --------------------------------------------------
        # Mark other candidates rejected
        # --------------------------------------------------

        other_results = list(
            session.execute(
                select(
                    ResolutionResult
                )
                .where(
                    ResolutionResult.mention_id
                    == mention.id,
                    ResolutionResult.id
                    != result.id,
                )
            )
            .scalars()
            .all()
        )

        for other_result in other_results:

            other_result.decision = (
                ResolutionDecision.REJECTED
            )

            other_result.reviewer_id = (
                reviewer_id
            )

        try:

            session.commit()
            session.refresh(result)

        except Exception:

            session.rollback()
            raise

        # --------------------------------------------------
        # Generate resolution summary after approval
        # --------------------------------------------------

        DocumentService.generate_resolution_summary(
            session=session,
            mention_id=mention.id,
        )

        return result

    # ------------------------------------------------------
    # REJECT
    # ------------------------------------------------------

    @staticmethod
    def reject_resolution(
        session: Session,
        result_id: int,
        reviewer_id: int,
        notes: str | None = None,
    ) -> ResolutionResult:

        result = (
            session.execute(
                select(
                    ResolutionResult
                )
                .where(
                    ResolutionResult.id
                    == result_id
                )
            )
            .scalar_one_or_none()
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resolution result not found",
            )

        mention = (
            session.execute(
                select(Mention)
                .where(
                    Mention.id
                    == result.mention_id
                )
            )
            .scalar_one_or_none()
        )

        if mention is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mention not found",
            )

        if (
            mention.resolution_status
            != ResolutionStatus.SENT_FOR_REVIEWER
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This mention is not currently "
                    "waiting for review."
                ),
            )

        if (
            result.decision
            != ResolutionDecision.REVIEW
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Only review candidates can "
                    "be rejected."
                ),
            )

        result.decision = (
            ResolutionDecision.REJECTED
        )

        result.reviewer_id = reviewer_id
        result.notes = notes

        mention.resolution_status = (
            ResolutionStatus.REJECTED
        )

        mention.resolved_business_id = None

        try:

            session.commit()
            session.refresh(result)

        except Exception:

            session.rollback()
            raise

        return result