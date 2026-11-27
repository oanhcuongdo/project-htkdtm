"""Idempotent seed script for the 5 demo RBAC users.

Usage:
    python -m app.scripts.seed_users

Requires SEED_DEFAULT_PASSWORD to be configured in the environment or .env.
"""

from __future__ import annotations

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.rbac import Role
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User
from app.services.channels import seed_default_channels

DEMO_SEED_USERS: tuple[tuple[str, str, Role], ...] = (
    ("admin@erp.demo", "Nguyễn Quản Trị", Role.ADMIN),
    ("manager@erp.demo", "Trần Thị Mai", Role.MANAGER),
    ("analyst@erp.demo", "Lê Văn Hùng", Role.PRICING_ANALYST),
    ("inventory@erp.demo", "Phạm Thu Hà", Role.INVENTORY_STAFF),
    ("viewer@erp.demo", "Đỗ Minh Khoa", Role.VIEWER),
)


def seed_demo_users(db: Session, default_password: str) -> tuple[int, int]:
    """Create missing demo users idempotently. Return (created_count, skipped_count)."""
    created = 0
    skipped = 0
    for email, full_name, role in DEMO_SEED_USERS:
        existing = db.scalar(select(User).where(User.email == email))
        if existing is not None:
            skipped += 1
            continue
        db.add(
            User(
                email=email,
                full_name=full_name,
                hashed_password=hash_password(default_password),
                role=role.value,
                is_active=True,
            )
        )
        created += 1
    if created:
        db.commit()
    return created, skipped


def main() -> int:
    """CLI entry point for seeding demo RBAC accounts."""
    settings = get_settings()
    password = (settings.SEED_DEFAULT_PASSWORD or "").strip()
    if not password:
        print(
            "Lỗi: Cần thiết lập biến môi trường SEED_DEFAULT_PASSWORD trước khi chạy seed_users.",
            file=sys.stderr,
        )
        return 1

    with SessionLocal() as db:
        u_created, u_skipped = seed_demo_users(db, password)
        c_created, c_skipped = seed_default_channels(db)
    print(
        f"Seed hoàn tất: users(tạo mới {u_created}, tồn tại {u_skipped}); "
        f"channels(tạo mới {c_created}, tồn tại {c_skipped})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
