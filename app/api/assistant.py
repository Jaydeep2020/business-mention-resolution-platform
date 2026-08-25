from fastapi import (
    APIRouter,
    Depends,
    Path,
)

from sqlalchemy.orm import Session

from app.db.database import (
    get_session,
)

from app.dependencies.auth import (
    require_roles,
)

from app.dependencies.rate_limit import (
    resolution_rate_limit,
)

from app.models.user import User

from app.schemas.assistant import (
    AssistantResolveRequest,
    AssistantResolutionResponse,
)

from app.services.assistant_service import (
    AssistantService,
)


router = APIRouter(
    prefix="/assistant",
    tags=["Smart Assistant"],
)


# ==========================================================
# SMART RESOLVE MENTION
# ==========================================================

@router.post(
    "/mentions/{mention_id}/resolve",
    response_model=(
        AssistantResolutionResponse
    ),
)
def smart_resolve_mention(

    data: AssistantResolveRequest,

    mention_id: int = Path(
        ...,
        gt=0,
    ),

    # Same rate limiter used around normal resolution.
    _rate_limit: None = Depends(
        resolution_rate_limit
    ),

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        require_roles(
            "admin",
            "reviewer",
        )
    ),
):

    return (
        AssistantService
        .resolve_mention(
            session=session,
            mention_id=mention_id,
            max_candidates=(
                data.max_candidates
            ),
        )
    )