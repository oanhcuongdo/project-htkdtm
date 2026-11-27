"""Kiểm tra lưu tài khoản và các ràng buộc dữ liệu trước khi viết API auth."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.users.models import User, UserRole


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    # Chỉ tạo schema trong DB kiểm thử; ứng dụng thật sẽ dùng Alembic ở phần migration.
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def make_user(**overrides):
    values = {
        "email": "customer@example.vn",
        "full_name": "Khách hàng",
        "hashed_password": "password-hash-from-auth-service",
    }
    return User(**(values | overrides))


def test_store_user_with_defaults_and_normalized_fields(db):
    started = datetime.now(UTC)
    user = make_user(email=" Customer@Example.VN ", full_name=" Khách hàng ")
    db.add(user)
    db.flush()

    assert user.id is not None
    assert user.email == "customer@example.vn"
    assert user.full_name == "Khách hàng"
    assert user.role == UserRole.CUSTOMER
    assert user.is_simulated is False
    assert started <= user.created_at <= datetime.now(UTC)

    db.commit()
    db.expire_all()
    stored = db.get(User, user.id)
    assert stored.email == "customer@example.vn"
    assert stored.hashed_password == "password-hash-from-auth-service"


@pytest.mark.parametrize("role", list(UserRole))
def test_roles_are_persisted_as_lowercase_values(db, role):
    user = make_user(role=role)
    db.add(user)
    db.commit()
    assert (
        db.execute(text("SELECT role FROM users WHERE id = :id"), {"id": user.id}).scalar_one()
        == role.value
    )
    db.expire_all()
    assert db.get(User, user.id).role is role


@pytest.mark.parametrize("role", ["owner", "CUSTOMER", "root"])
def test_database_rejects_unknown_roles_even_for_raw_sql(db, role):
    with pytest.raises(IntegrityError):
        db.execute(
            text(
                "INSERT INTO users (email, full_name, hashed_password, role) VALUES (:email, :name, :hash, :role)"
            ),
            {"email": "invalid@example.vn", "name": "Invalid", "hash": "hash", "role": role},
        )
    db.rollback()


def test_duplicate_normalized_email_is_rejected(db):
    db.add(make_user())
    db.commit()
    db.add(make_user(email=" CUSTOMER@EXAMPLE.VN "))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
    assert db.query(User).count() == 1


@pytest.mark.parametrize("missing", ["email", "full_name", "hashed_password"])
def test_required_fields_are_enforced_by_database(db, missing):
    values = {"email": "required@example.vn", "full_name": "Required", "hashed_password": "hash"}
    values.pop(missing)
    db.add(User(**values))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize("field", ["email", "full_name"])
def test_blank_identity_fields_are_rejected(field):
    with pytest.raises(ValueError):
        make_user(**{field: "   "})


def test_simulated_account_flag_can_be_persisted(db):
    user = make_user(is_simulated=True)
    db.add(user)
    db.commit()
    db.expire_all()
    assert db.get(User, user.id).is_simulated is True


def test_database_defaults_apply_to_raw_inserts(db):
    db.execute(
        text(
            "INSERT INTO users (email, full_name, hashed_password) VALUES ('raw@example.vn', 'Raw', 'hash')"
        )
    )
    db.commit()
    stored = db.query(User).filter_by(email="raw@example.vn").one()
    assert stored.role is UserRole.CUSTOMER
    assert stored.is_simulated is False
    assert stored.created_at is not None
