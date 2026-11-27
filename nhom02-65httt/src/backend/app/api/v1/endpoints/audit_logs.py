"""Audit log query endpoint protected by AUDIT_READ permission."""

from __future__ import annotations

import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.rbac import Permission
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogRead
from app.schemas.common import Envelope, PageMeta

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=Envelope[list[AuditLogRead]])
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None, alias="resourceType"),
    q: str | None = Query(default=None),
    _: User = Depends(require_permission(Permission.AUDIT_READ)),
    db: Session = Depends(get_db),
) -> Envelope[list[AuditLogRead]]:
    """Return a paginated, filterable stream of system audit events."""
    filters = []
    if action and action.strip():
        filters.append(AuditLog.action == action.strip())
    if resource_type and resource_type.strip():
        filters.append(AuditLog.resource_type == resource_type.strip())
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        filters.append(
            or_(
                AuditLog.actor.ilike(pattern),
                AuditLog.action.ilike(pattern),
                AuditLog.resource_type.ilike(pattern),
                AuditLog.reason.ilike(pattern),
                AuditLog.request_id.ilike(pattern),
                AuditLog.before_summary.ilike(pattern),
                AuditLog.after_summary.ilike(pattern),
            )
        )

    total = db.scalar(select(func.count()).select_from(AuditLog).where(*filters)) or 0
    total_pages = max(1, math.ceil(total / page_size))

    stmt = (
        select(AuditLog)
        .where(*filters)
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    entries = db.scalars(stmt).all()

    return Envelope(
        data=[AuditLogRead.model_validate(entry) for entry in entries],
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )
