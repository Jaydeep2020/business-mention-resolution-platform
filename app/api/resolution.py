from fastapi import (
    APIRouter,
    Depends,
    Path,
    Query,
)

from sqlalchemy.orm import Session

from app.db.database import (
    get_session,
)

from app.dependencies.auth import (
    get_current_user,
    require_roles,
)

from app.dependencies.rate_limit import (
    resolution_rate_limit,
)

from app.models.user import User

from app.schemas.resolution import (
    ResolveMentionRequest,
    ResolutionResponse,
    ResolutionResultListResponse,
    ResolutionResultResponse,
    ReviewDecisionRequest,
)

from app.services.resolution_service import (
    ResolutionService,
)


router = APIRouter(
    prefix="/resolution",
    tags=["Resolution"],
)


# ==========================================================
# RESOLVE MENTION
# ==========================================================

@router.post(
    "/mentions/{mention_id}",
    response_model=ResolutionResponse,
)
def resolve_mention(

    data: ResolveMentionRequest,

    mention_id: int = Path(
        ...,
        gt=0,
    ),

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
        ResolutionService
        .resolve_mention(
            session=session,
            mention_id=mention_id,
            max_candidates=(
                data.max_candidates
            ),
        )
    )


# ==========================================================
# GET RESOLUTION RESULTS
# ==========================================================

@router.get(
    "/results",
    response_model=ResolutionResultListResponse,
)
def get_resolution_results(

    page: int = Query(
        default=1,
        ge=1,
    ),

    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    return (
        ResolutionService
        .get_resolution_results(
            session=session,
            page=page,
            page_size=page_size,
        )
    )


# ==========================================================
# REVIEW QUEUE
# ==========================================================

@router.get(
    "/review-queue",
    response_model=ResolutionResultListResponse,
)
def get_review_queue(

    page: int = Query(
        default=1,
        ge=1,
    ),

    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
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
        ResolutionService
        .get_review_queue(
            session=session,
            page=page,
            page_size=page_size,
        )
    )


# ==========================================================
# APPROVE
# ==========================================================

@router.post(
    "/results/{result_id}/approve",
    response_model=ResolutionResultResponse,
)
def approve_resolution(

    data: ReviewDecisionRequest,

    result_id: int = Path(
        ...,
        gt=0,
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
        ResolutionService
        .approve_resolution(
            session=session,
            result_id=result_id,
            reviewer_id=current_user.id,
            notes=data.notes,
        )
    )


# ==========================================================
# REJECT
# ==========================================================

@router.post(
    "/results/{result_id}/reject",
    response_model=ResolutionResultResponse,
)
def reject_resolution(

    data: ReviewDecisionRequest,

    result_id: int = Path(
        ...,
        gt=0,
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
        ResolutionService
        .reject_resolution(
            session=session,
            result_id=result_id,
            reviewer_id=current_user.id,
            notes=data.notes,
        )
    )