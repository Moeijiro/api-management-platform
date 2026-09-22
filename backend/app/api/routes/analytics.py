"""Usage analytics for the dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.analytics import UsageOverview
from app.services import analytics

router = APIRouter(prefix="/api/usage", tags=["analytics"])


@router.get("", response_model=UsageOverview, summary="Dashboard usage overview")
def usage(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UsageOverview:
    return UsageOverview(**analytics.overview(db, user.id))
