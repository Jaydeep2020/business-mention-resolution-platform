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

from app.models.enums import ResolutionStatus
from app.models.user import User

from app.schemas.mention import (
    MentionCreate,
    MentionListResponse,
    MentionResponse,
    MentionUpdate,
)

from app.services.mention_service import (
    MentionService,
)


router = APIRouter(
    prefix="/mentions",
    tags=["Mentions"],
)


@router.post(
    "",
    response_model=MentionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_mention(

    data: MentionCreate,

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

    return MentionService.create_mention(
        session=session,
        data=data,
    )


@router.get(
    "",
    response_model=MentionListResponse,
)
def list_mentions(

    page: int = Query(
        default=1,
        ge=1,
    ),

    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),

    search: str | None = Query(
        default=None,
        max_length=255,
    ),

    status_filter: ResolutionStatus | None = Query(
        default=None,
    ),

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    return MentionService.get_mentions(
        session=session,
        page=page,
        page_size=page_size,
        search=search,
        status_filter=status_filter,
    )


@router.get(
    "/{mention_id}",
    response_model=MentionResponse,
)
def get_mention(

    mention_id: int,

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    return MentionService.get_mention(
        session=session,
        mention_id=mention_id,
    )


@router.put(
    "/{mention_id}",
    response_model=MentionResponse,
)
def update_mention(

    mention_id: int,
    data: MentionUpdate,

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

    return MentionService.update_mention(
        session=session,
        mention_id=mention_id,
        data=data,
    )


@router.delete(
    "/{mention_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_mention(

    mention_id: int,

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        require_roles("admin")
    ),
):

    MentionService.delete_mention(
        session=session,
        mention_id=mention_id,
    )

    return None