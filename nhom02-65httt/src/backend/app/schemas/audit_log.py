"""Audit log response schema."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.schemas.common import ApiModel


class AuditLogRead(ApiModel):
    """Public audit log entry matching frontend AuditLog shape."""

    id: UUID
    actor: str
    action: str
    resource_type: str
    reason: str | None
    request_id: str
    before_summary: str | None
    after_summary: str | None
    created_at: datetime
