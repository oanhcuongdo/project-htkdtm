"""Immutable audit logging service."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record_audit_log(
    db: Session,
    *,
    actor: str,
    action: str,
    resource_type: str,
    reason: str | None = None,
    request_id: str | None = None,
    before_summary: str | None = None,
    after_summary: str | None = None,
) -> AuditLog:
    """Attach a new AuditLog entry to the active DB transaction (caller commits)."""
    entry = AuditLog(
        actor=actor,
        action=action,
        resource_type=resource_type,
        reason=reason,
        request_id=request_id or f"req-{uuid.uuid4().hex[:8]}",
        before_summary=before_summary,
        after_summary=after_summary,
    )
    db.add(entry)
    return entry
