from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    Path as FastAPIPath,
    Query,
)

from fastapi.responses import (
    FileResponse,
)

from sqlalchemy.orm import Session

from document_service.db.database import (
    get_session,
)

from document_service.dependencies.auth import (
    AuthenticatedUser,
    get_current_user,
    require_roles,
)

from document_service.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    MonthlyReportRequest,
    MonthlyReportResponse,
)

from document_service.services.document_service import (
    DocumentService,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# ==========================================================
# LIST
# ==========================================================

@router.get(
    "",
    response_model=(
        DocumentListResponse
    ),
)
def list_documents(

    page: int = Query(
        1,
        ge=1,
    ),

    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),

    document_type: (
        str | None
    ) = Query(
        default=None,
        max_length=50,
    ),

    session: Session = Depends(
        get_session
    ),

    current_user: (
        AuthenticatedUser
    ) = Depends(
        get_current_user
    ),
):

    return (
        DocumentService
        .get_documents(
            session=session,
            page=page,
            page_size=page_size,
            document_type=(
                document_type
            ),
        )
    )


# ==========================================================
# OPTIONAL MANUAL/RETRY SUMMARY GENERATION
# ==========================================================

@router.post(
    "/resolution-summary/{mention_id}",
    response_model=(
        DocumentResponse
    ),
)
def generate_resolution_summary(

    mention_id: int = FastAPIPath(
        ...,
        gt=0,
    ),

    session: Session = Depends(
        get_session
    ),

    current_user: (
        AuthenticatedUser
    ) = Depends(
        require_roles(
            "admin",
            "reviewer",
        )
    ),
):

    return (
        DocumentService
        .generate_resolution_summary(
            session=session,
            mention_id=mention_id,
        )
    )


# ==========================================================
# MONTHLY REPORT
# ==========================================================

@router.post(
    "/monthly-report",
    response_model=(
        MonthlyReportResponse
    ),
)
def generate_monthly_report(

    data: MonthlyReportRequest,

    session: Session = Depends(
        get_session
    ),

    current_user: (
        AuthenticatedUser
    ) = Depends(
        require_roles(
            "admin",
            "reviewer",
        )
    ),
):

    return (
        DocumentService
        .generate_monthly_report(
            session=session,
            month=data.month,
        )
    )


# ==========================================================
# DETAILS
# ==========================================================

@router.get(
    "/{document_id}",
    response_model=(
        DocumentResponse
    ),
)
def get_document(

    document_id: int = FastAPIPath(
        ...,
        gt=0,
    ),

    session: Session = Depends(
        get_session
    ),

    current_user: (
        AuthenticatedUser
    ) = Depends(
        get_current_user
    ),
):

    return (
        DocumentService
        .get_document(
            session=session,
            document_id=document_id,
        )
    )


# ==========================================================
# DOWNLOAD
# ==========================================================

@router.get(
    "/{document_id}/download",
)
def download_document(

    document_id: int = FastAPIPath(
        ...,
        gt=0,
    ),

    session: Session = Depends(
        get_session
    ),

    current_user: (
        AuthenticatedUser
    ) = Depends(
        get_current_user
    ),
):

    document = (
        DocumentService
        .get_document(
            session=session,
            document_id=document_id,
        )
    )

    file_path = (
        DocumentService
        .get_document_path(
            document
        )
    )

    return FileResponse(
        path=str(
            file_path
        ),
        media_type=(
            "application/pdf"
        ),
        filename=Path(
            file_path
        ).name,
    )