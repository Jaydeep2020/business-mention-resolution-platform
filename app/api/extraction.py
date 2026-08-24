from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.db.database import (
    get_session,
)

from app.dependencies.auth import (
    require_roles,
)

from app.models.user import (
    User,
)

from app.schemas.extraction import (
    ExtractMentionsRequest,
    ExtractionResponse,
)

from app.services.mention_extraction_service import (
    MentionExtractionService,
)


router = APIRouter(
    prefix="/extraction",
    tags=["Mention Extraction"],
)


# ==========================================================
# EXTRACT BUSINESS MENTIONS
# ==========================================================

@router.post(
    "/mentions",
    response_model=ExtractionResponse,
)
def extract_mentions(

    data: ExtractMentionsRequest,

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
        MentionExtractionService
        .extract_mentions(
            session=session,
            data=data,
        )
    )