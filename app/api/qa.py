from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.db.database import (
    get_session,
)

from app.dependencies.auth import (
    get_current_user,
)

from app.models.user import (
    User,
)

from app.schemas.qa import (
    CatalogQuestionRequest,
    CatalogQAResponse,
)

from app.services.catalog_qa_service import (
    CatalogQAService,
)


router = APIRouter(
    prefix="/qa",
    tags=["Catalog Question Answering"],
)


# ==========================================================
# ASK CATALOG QUESTION
# ==========================================================

@router.post(
    "/ask",
    response_model=CatalogQAResponse,
)
def ask_catalog_question(

    data: CatalogQuestionRequest,

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    return (
        CatalogQAService
        .ask_question(
            session=session,
            data=data,
        )
    )