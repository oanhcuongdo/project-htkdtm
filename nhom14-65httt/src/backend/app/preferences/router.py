"""API hồ sơ khẩu vị khách hàng; bỏ qua onboarding không tạo bản ghi."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.preferences import service
from app.preferences.schemas import PreferenceInput, PreferenceOut
from app.users.models import User, UserRole

router = APIRouter(prefix="/preferences", tags=["preferences"])
Database = Annotated[Session, Depends(get_db)]
Customer = Annotated[User, Depends(require_role(UserRole.CUSTOMER))]


@router.get("/", response_model=PreferenceOut)
def detail(db: Database, user: Customer):
    return service.get_preference(db, user.id)


@router.put("/", response_model=PreferenceOut)
def save(payload: PreferenceInput, db: Database, user: Customer):
    return service.save_preference(db, user.id, payload)
