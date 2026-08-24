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

from app.schemas.category import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdate,
)

from app.services.category_service import (
    CategoryService,
)


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    data: CategoryCreate,

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        require_roles("admin")
    ),
):

    return CategoryService.create_category(
        session=session,
        data=data,
    )


@router.get(
    "",
    response_model=CategoryListResponse,
)
def list_categories(

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

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    return CategoryService.get_categories(
        session=session,
        page=page,
        page_size=page_size,
        search=search,
    )


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
)
def get_category(
    category_id: int,

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    return CategoryService.get_category(
        session=session,
        category_id=category_id,
    )


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
)
def update_category(
    category_id: int,
    data: CategoryUpdate,

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        require_roles("admin")
    ),
):

    return CategoryService.update_category(
        session=session,
        category_id=category_id,
        data=data,
    )


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_category(
    category_id: int,

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

    CategoryService.delete_category(
        session=session,
        category_id=category_id,
    )

    return None