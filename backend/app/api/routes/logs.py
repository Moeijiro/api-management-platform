"""Request log browsing."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models import RequestLog, User
from app.schemas.request_log import RequestLogOut, RequestLogPage

router = APIRouter(prefix="/api/logs", tags=["request logs"])


@router.get("", response_model=RequestLogPage, summary="Browse request logs")
def list_logs(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status_code: int | None = Query(default=None, ge=100, le=599, alias="status"),
    status_class: str | None = Query(
        default=None, pattern="^(2xx|4xx|5xx)$", description="Coarse status filter."
    ),
    method: str | None = Query(default=None, max_length=8),
    api_key_id: int | None = Query(default=None, ge=1),
) -> RequestLogPage:
    where = [RequestLog.user_id == user.id]
    if status_code:
        where.append(RequestLog.status_code == status_code)
    if status_class:
        lower = int(status_class[0]) * 100
        where.append(RequestLog.status_code.between(lower, lower + 99))
    if method:
        where.append(RequestLog.method == method.upper())
    if api_key_id:
        where.append(RequestLog.api_key_id == api_key_id)

    items = db.execute(
        select(RequestLog)
        .where(*where)
        .order_by(RequestLog.created_at.desc(), RequestLog.id.desc())
        .offset(offset)
        .limit(limit)
    ).scalars().all()
    total = db.execute(
        select(func.count()).select_from(RequestLog).where(*where)
    ).scalar_one()

    return RequestLogPage(
        items=[RequestLogOut.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )
