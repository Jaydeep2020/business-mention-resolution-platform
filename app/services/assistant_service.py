from fastapi import (
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.core.config import (
    settings,
)

from app.graphs.resolution_assistant_graph import (
    resolution_assistant_graph,
)


class AssistantService:

    @staticmethod
    def resolve_mention(
        session: Session,
        mention_id: int,
        max_candidates: int = 5,
    ) -> dict:

        # ==================================================
        # DEFENSIVE VALIDATION
        # ==================================================

        if (
            not isinstance(
                mention_id,
                int,
            )
            or isinstance(
                mention_id,
                bool,
            )
            or mention_id < 1
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "mention_id must be "
                    "a positive integer."
                ),
            )

        if (
            not isinstance(
                max_candidates,
                int,
            )
            or isinstance(
                max_candidates,
                bool,
            )
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "max_candidates must "
                    "be an integer."
                ),
            )

        if (
            max_candidates < 2
            or max_candidates > 10
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "max_candidates must be "
                    "between 2 and 10."
                ),
            )

        # Keep server-side maximum under control.
        max_candidates = min(
            max_candidates,
            max(
                2,
                settings
                .ASSISTANT_MAX_CANDIDATES,
            ),
        )

        # ==================================================
        # RUN LANGGRAPH
        # ==================================================

        result = (
            resolution_assistant_graph
            .invoke(
                {
                    "session": session,

                    "mention_id": (
                        mention_id
                    ),

                    "max_candidates": (
                        max_candidates
                    ),

                    "workflow_steps": [],
                }
            )
        )

        response = result.get(
            "response"
        )

        if response is None:

            raise HTTPException(
                status_code=(
                    status
                    .HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "Smart assistant did not "
                    "produce a final result."
                ),
            )

        return response