from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from document_service.db.database import (
    get_session,
)

from document_service.dependencies.internal_auth import (
    verify_internal_service,
)

from document_service.schemas.document import (
    DocumentResponse,
    ResolutionSummaryRequest,
)

from document_service.services.document_service import (
    DocumentService,
)


router = APIRouter(
    prefix="/internal",
    tags=["Internal"],
    dependencies=[
        Depends(
            verify_internal_service
        )
    ],
)


@router.post(
    "/resolution-summary",
    response_model=(
        DocumentResponse
    ),
)
def generate_resolution_summary(

    data: ResolutionSummaryRequest,

    session: Session = Depends(
        get_session
    ),
):

    return (
        DocumentService
        .generate_resolution_summary(
            session=session,
            mention_id=(
                data.mention_id
            ),
        )
    )