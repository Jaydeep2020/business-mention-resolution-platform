from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from app.db.database import get_session

from app.dependencies.auth import (
    get_current_user,
    require_roles,
)

from app.models.user import User

from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    MonthlyReportRequest,
    MonthlyReportResponse,
)

from app.services.document_service import (
    DocumentService,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# ==========================================================
# LIST DOCUMENTS
# ==========================================================

@router.get(
    "",
    response_model=DocumentListResponse,
)
def list_documents(

    page: int = Query(
        default=1,
        ge=1,
    ),

    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),

    document_type: str | None = Query(
        default=None,
        max_length=50,
    ),

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    return DocumentService.get_documents(
        session=session,
        page=page,
        page_size=page_size,
        document_type=document_type,
    )

# ==========================================================
# GENERATE MONTHLY REPORT
# ==========================================================

@router.post(
    "/monthly-report",
    response_model=MonthlyReportResponse,
)
def generate_monthly_report(

    data: MonthlyReportRequest,

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
        DocumentService
        .generate_monthly_report(
            session=session,
            month=data.month,
        )
    )


# ==========================================================
# GET DOCUMENT DETAILS
# ==========================================================

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(

    document_id: int,

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    return DocumentService.get_document(
        session=session,
        document_id=document_id,
    )


# ==========================================================
# DOWNLOAD DOCUMENT
# ==========================================================

@router.get(
    "/{document_id}/download",
)
def download_document(

    document_id: int,

    session: Session = Depends(
        get_session
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    document = (
        DocumentService.get_document(
            session=session,
            document_id=document_id,
        )
    )

    file_path = (
        DocumentService.get_document_path(
            document
        )
    )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=Path(
            file_path
        ).name,
    )