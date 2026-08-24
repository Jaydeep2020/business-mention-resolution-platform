from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)

from sqlalchemy.orm import Session

from app.db.database import get_session

from app.dependencies.auth import (
    get_current_user,
    require_roles,
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
# RESOLVE A MENTION
# ==========================================================

@router.post(
    "/mentions/{mention_id}",
    response_model=ResolutionResponse,
)
def resolve_mention(
    mention_id: int,

    data: ResolveMentionRequest,

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

    return ResolutionService.resolve_mention(
        session=session,
        mention_id=mention_id,
        max_candidates=data.max_candidates,
    )


# ==========================================================
# GET ALL RESOLUTION RESULTS
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

    return ResolutionService.get_resolution_results(
        session=session,
        page=page,
        page_size=page_size,
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

    return ResolutionService.get_review_queue(
        session=session,
        page=page,
        page_size=page_size,
    )


# ==========================================================
# APPROVE
# ==========================================================

@router.post(
    "/results/{result_id}/approve",
    response_model=ResolutionResultResponse,
)
def approve_resolution(

    result_id: int,

    data: ReviewDecisionRequest,

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

    result = (
        ResolutionService.approve_resolution(
            session=session,
            result_id=result_id,
            reviewer_id=current_user.id,
            notes=data.notes,
        )
    )

    return result


# ==========================================================
# REJECT
# ==========================================================

@router.post(
    "/results/{result_id}/reject",
    response_model=ResolutionResultResponse,
)
def reject_resolution(

    result_id: int,

    data: ReviewDecisionRequest,

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

    result = (
        ResolutionService.reject_resolution(
            session=session,
            result_id=result_id,
            reviewer_id=current_user.id,
            notes=data.notes,
        )
    )

    return result