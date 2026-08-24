from fastapi import (
    HTTPException,
    status,
)

from sqlalchemy import (
    func,
    select,
)

from sqlalchemy.orm import Session

from app.core.nlp import (
    GLINER_MODEL_NAME,
    extract_business_entities,
)

from app.models.mention import (
    Mention,
)

from app.models.enums import (
    ResolutionStatus,
)

from app.schemas.extraction import (
    ExtractMentionsRequest,
)


class MentionExtractionService:

    # ======================================================
    # FIND EXISTING MENTION
    # ======================================================

    @staticmethod
    def find_existing_mention(
        session: Session,
        mention_text: str,
        source_id: str | None,
        source_type,
    ) -> Mention | None:
        """
        Prevent duplicate Mention rows when the same
        source is processed again.

        Example:

        source_id = review-123
        mention   = Starbucks

        If that pair already exists, reuse it.
        """

        # Without source_id we cannot reliably know
        # whether this is the same source as a previous
        # extraction request.
        if source_id is None:
            return None

        mention = (
            session.execute(
                select(Mention)
                .where(
                    Mention.source_id
                    == source_id,

                    Mention.source_type
                    == source_type,

                    func.lower(
                        func.trim(
                            Mention.text
                        )
                    )
                    == mention_text
                    .strip()
                    .lower(),
                )
                .limit(1)
            )
            .scalar_one_or_none()
        )

        return mention


    # ======================================================
    # EXTRACT MENTIONS
    # ======================================================

    @classmethod
    def extract_mentions(
        cls,
        session: Session,
        data: ExtractMentionsRequest,
    ) -> dict:

        # --------------------------------------------------
        # Defensive validation
        # --------------------------------------------------

        source_text = (
            data.text.strip()
        )

        if not source_text:

            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "Source text cannot be empty."
                ),
            )

        # --------------------------------------------------
        # NLP extraction
        # --------------------------------------------------

        try:

            extracted_entities = (
                extract_business_entities(
                    source_text
                )
            )

        except RuntimeError as exc:

            # Usually means en_core_web_sm
            # wasn't installed.
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_503_SERVICE_UNAVAILABLE
                ),
                detail=str(exc),
            )

        # --------------------------------------------------
        # Preview mode
        # --------------------------------------------------

        if not data.save_mentions:

            return {
                "source_id": (
                    data.source_id
                ),
                "source_type": (
                    data.source_type
                ),
                "model": (
                    GLINER_MODEL_NAME
                ),
                "saved": False,
                "total_extracted": len(
                    extracted_entities
                ),
                "created_count": 0,
                "reused_count": 0,
                "mentions": [
                    {
                        **entity,
                        "mention_id": None,
                        "created": False,
                    }
                    for entity
                    in extracted_entities
                ],
            }

        # --------------------------------------------------
        # Save mode
        # --------------------------------------------------

        response_mentions = []

        created_count = 0
        reused_count = 0

        try:

            for entity in extracted_entities:

                mention_text = (
                    entity["text"]
                )

                # ------------------------------------------
                # Avoid duplicate rows
                # ------------------------------------------

                existing_mention = (
                    cls.find_existing_mention(
                        session=session,
                        mention_text=mention_text,
                        source_id=data.source_id,
                        source_type=(
                            data.source_type
                        ),
                    )
                )

                if existing_mention:

                    reused_count += 1

                    response_mentions.append(
                        {
                            **entity,
                            "mention_id": (
                                existing_mention.id
                            ),
                            "created": False,
                        }
                    )

                    continue

                # ------------------------------------------
                # Create new Mention
                # ------------------------------------------

                mention = Mention(
                    text=mention_text,
                    source_text=source_text,
                    source_type=(
                        data.source_type
                    ),
                    source_id=(
                        data.source_id
                    ),
                    resolution_status=(
                        ResolutionStatus.PENDING
                    ),
                    resolved_business_id=None,
                    confidence_score=None,
                )

                session.add(
                    mention
                )

                # Get database-generated ID
                # without committing yet.
                session.flush()

                created_count += 1

                response_mentions.append(
                    {
                        **entity,
                        "mention_id": (
                            mention.id
                        ),
                        "created": True,
                    }
                )

            # Commit all newly extracted mentions
            # together.
            session.commit()

        except Exception:

            session.rollback()

            raise

        return {
            "source_id": (
                data.source_id
            ),
            "source_type": (
                data.source_type
            ),

            "model": GLINER_MODEL_NAME,

            "saved": True,
            "total_extracted": len(
                extracted_entities
            ),
            "created_count": (
                created_count
            ),
            "reused_count": (
                reused_count
            ),
            "mentions": (
                response_mentions
            ),
        }