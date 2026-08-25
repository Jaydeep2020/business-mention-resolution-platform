from fastapi import (
    APIRouter,
    Depends,
    Path,
)

from sqlalchemy.orm import Session

from app.db.database import (
    get_session,
)

from app.dependencies.internal_auth import (
    verify_internal_service,
)

from app.schemas.internal import (
    MonthlyReportDataResponse,
    ResolutionSnapshotResponse,
)

from app.services.reporting_service import (
    ReportingService,
)

from app.services.resolution_snapshot_service import (
    ResolutionSnapshotService,
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


# ==========================================================
# RESOLUTION SNAPSHOT
# ==========================================================

@router.get(
    "/resolutions/{mention_id}/snapshot",
    response_model=(
        ResolutionSnapshotResponse
    ),
)
def resolution_snapshot(

    mention_id: int = Path(
        ...,
        gt=0,
    ),

    session: Session = Depends(
        get_session
    ),
):

    return (
        ResolutionSnapshotService
        .get_resolution_snapshot(
            session=session,
            mention_id=mention_id,
        )
    )


# ==========================================================
# MONTHLY REPORT DATA
# ==========================================================

@router.get(
    "/reporting/monthly/{month}",
    response_model=(
        MonthlyReportDataResponse
    ),
)
def monthly_report_data(

    month: str,

    session: Session = Depends(
        get_session
    ),
):

    return (
        ReportingService
        .get_monthly_report_data(
            session=session,
            month=month,
        )
    )