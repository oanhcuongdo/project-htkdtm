"""User administration endpoints protected by RBAC."""

from __future__ import annotations

import math
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_any_permission, require_permission
from app.core.errors import ConflictError, NotFoundError
from app.core.rbac import Permission, Role
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import Envelope, PageMeta
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.audit import record_audit_log

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=Envelope[list[UserRead]])
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    q: str | None = Query(default=None),
    role: Role | None = Query(default=None),
    _: User = Depends(require_any_permission(Permission.USER_MANAGE, Permission.SETTINGS_READ)),
    db: Session = Depends(get_db),
) -> Envelope[list[UserRead]]:
    """Return a paginated, searchable list of system users."""
    filters = []
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        filters.append(or_(User.email.ilike(pattern), User.full_name.ilike(pattern)))
    if role is not None:
        filters.append(User.role == role.value)

    total = db.scalar(select(func.count()).select_from(User).where(*filters)) or 0
    total_pages = max(1, math.ceil(total / page_size))

    stmt = (
        select(User)
        .where(*filters)
        .order_by(User.created_at.desc(), User.email.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    users = db.scalars(stmt).all()

    return Envelope(
        data=[UserRead.model_validate(user) for user in users],
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.post("", response_model=Envelope[UserRead], status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_permission(Permission.USER_MANAGE)),
    db: Session = Depends(get_db),
) -> Envelope[UserRead]:
    """Create a new user with an initial role and hashed password."""
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise ConflictError("Email đã tồn tại trong hệ thống.")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role.value,
        is_active=True,
    )
    db.add(user)
    record_audit_log(
        db,
        actor=current_user.full_name,
        action="CREATE_USER",
        resource_type="user",
        after_summary=f"{user.email} ({user.role})",
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Email đã tồn tại trong hệ thống.") from exc
    db.refresh(user)
    return Envelope(data=UserRead.model_validate(user))


@router.patch("/{user_id}", response_model=Envelope[UserRead])
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    current_user: User = Depends(require_permission(Permission.USER_MANAGE)),
    db: Session = Depends(get_db),
) -> Envelope[UserRead]:
    """Update a user's display name, role, or activation state."""
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("Không tìm thấy người dùng.")

    updates = payload.model_dump(exclude_unset=True)
    if user.id == current_user.id:
        if updates.get("is_active") is False:
            raise ConflictError("Không thể tự vô hiệu hóa tài khoản của chính mình.")
        new_role = updates.get("role")
        if new_role is not None and new_role.value != user.role:
            raise ConflictError("Không thể tự thay đổi vai trò của chính mình.")

    before_summary = f"fullName={user.full_name}, role={user.role}, isActive={user.is_active}"

    if "full_name" in updates and updates["full_name"] is not None:
        user.full_name = updates["full_name"]
    if "role" in updates and updates["role"] is not None:
        user.role = updates["role"].value
    if "is_active" in updates and updates["is_active"] is not None:
        user.is_active = updates["is_active"]

    record_audit_log(
        db,
        actor=current_user.full_name,
        action="UPDATE_USER",
        resource_type="user",
        before_summary=before_summary,
        after_summary=f"fullName={user.full_name}, role={user.role}, isActive={user.is_active}",
    )
    db.commit()
    db.refresh(user)
    return Envelope(data=UserRead.model_validate(user))
