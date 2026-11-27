"""API đánh giá món trong đơn hoàn tất của customer."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.reviews import service
from app.reviews.schemas import ReviewCreate, ReviewOut
from app.users.models import User, UserRole

router = APIRouter(tags=["reviews"])
Database = Annotated[Session, Depends(get_db)]
Customer = Annotated[User, Depends(require_role(UserRole.CUSTOMER))]
OrderId = Annotated[int, Path(gt=0, le=2**31 - 1)]


@router.post("/orders/{order_id}/review", response_model=ReviewOut, status_code=201)
def create(order_id: OrderId, payload: ReviewCreate, db: Database, user: Customer):
    return service.create_review(db, user.id, order_id, payload)
