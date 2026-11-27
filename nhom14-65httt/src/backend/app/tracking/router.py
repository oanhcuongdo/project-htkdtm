"""API ghi nhận sự kiện khách hàng theo batch."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.tracking import service
from app.tracking.schemas import EventBatch, EventBatchResult
from app.users.models import User, UserRole

router = APIRouter(prefix="/tracking", tags=["tracking"])
Database = Annotated[Session, Depends(get_db)]
Customer = Annotated[User, Depends(require_role(UserRole.CUSTOMER))]


@router.post("/events", response_model=EventBatchResult)
def events(payload: EventBatch, db: Database, user: Customer):
    return service.ingest_events(db, user.id, payload)
