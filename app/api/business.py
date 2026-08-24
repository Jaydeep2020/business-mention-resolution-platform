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

from app.schemas.business import (
    BusinessCreate,
    BusinessListResponse,
    BusinessResponse,
    BusinessUpdate,
)

from app.services.business_service import (
    BusinessService,
)


router = APIRouter(
    prefix="/businesses",
    tags=["Businesses"],
)


@router.post(
    "",
    response_model=BusinessResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_business(
    data: BusinessCreate,

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        require_roles("admin")
    ),
):

    return BusinessService.create_business(
        session=session,
        data=data,
    )


@router.get(
    "",
    response_model=BusinessListResponse,
)
def list_businesses(

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
        max_length=100,
    ),

    city: str | None = Query(
        default=None,
        max_length=100,
    ),

    category_id: int | None = Query(
        default=None,
        ge=1,
    ),

    is_verified: bool | None = Query(
        default=None
    ),

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    return BusinessService.get_businesses(
        session=session,
        page=page,
        page_size=page_size,
        search=search,
        city=city,
        category_id=category_id,
        is_verified=is_verified,
    )


@router.get(
    "/{business_pk}",
    response_model=BusinessResponse,
)
def get_business(
    business_pk: int,

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    return BusinessService.get_business(
        session=session,
        business_pk=business_pk,
    )


@router.put(
    "/{business_pk}",
    response_model=BusinessResponse,
)
def update_business(
    business_pk: int,
    data: BusinessUpdate,

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        require_roles("admin")
    ),
):

    return BusinessService.update_business(
        session=session,
        business_pk=business_pk,
        data=data,
    )


@router.delete(
    "/{business_pk}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_business(
    business_pk: int,

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

    BusinessService.delete_business(
        session=session,
        business_pk=business_pk,
    )

    return None