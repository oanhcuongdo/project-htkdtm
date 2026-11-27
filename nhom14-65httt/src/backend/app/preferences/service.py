"""Đọc và thay toàn bộ hồ sơ khẩu vị của tài khoản customer hiện tại."""

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.exceptions import ForbiddenError, NotFoundError
from app.preferences.models import Preference
from app.preferences.schemas import PreferenceInput, PreferenceOut
from app.users.models import User, UserRole


def get_preference(db: Session, user_id: int) -> PreferenceOut:
    user = db.get(User, user_id, populate_existing=True)
    if user is None or user.role != UserRole.CUSTOMER:
        raise ForbiddenError()
    row = db.get(Preference, user_id)
    if row is None:
        raise NotFoundError("Chưa có hồ sơ khẩu vị.")
    return PreferenceOut.model_validate(row)


def save_preference(db: Session, user_id: int, payload: PreferenceInput) -> PreferenceOut:
    try:
        # Khóa User để tuần tự hóa lần tạo đầu tiên trên PostgreSQL.
        user = db.get(User, user_id, with_for_update=True, populate_existing=True)
        if user is None or user.role != UserRole.CUSTOMER:
            raise ForbiddenError()
        row = db.get(Preference, user_id, with_for_update=True, populate_existing=True)
        if row is None:
            row = Preference(user_id=user_id)
            db.add(row)
        for field, value in payload.model_dump().items():
            setattr(row, field, value)
        db.commit()
    except IntegrityError:
        db.rollback()
        # Tranh chấp lần tạo đầu: cập nhật hồ sơ hiện có trong transaction mới.
        row = db.get(Preference, user_id, with_for_update=True, populate_existing=True)
        if row is None:
            raise
        try:
            for field, value in payload.model_dump().items():
                setattr(row, field, value)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise
    except (ForbiddenError, SQLAlchemyError):
        db.rollback()
        raise
    db.refresh(row)
    return PreferenceOut.model_validate(row)
