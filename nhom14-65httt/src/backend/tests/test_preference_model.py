"""Kiểm tra liên kết tài khoản, lưu khẩu vị và cập nhật các danh sách JSON."""

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.preferences.models import Preference
from app.users.models import User


@pytest.fixture
def db():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    # Chỉ tạo schema cho DB kiểm thử; không tạo bảng trong DB ứng dụng.
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            User(
                id=user_id,
                email=f"customer{user_id}@example.vn",
                full_name=f"Khách {user_id}",
                hashed_password="password-hash-from-auth-service",
            )
            for user_id in (1, 2)
        )
        session.commit()
        yield session
    engine.dispose()


def test_store_five_answers_and_link_to_account(db):
    db.add(
        Preference(
            user_id=1,
            regions=[" Bắc ", "Nam", "bắc"],
            spice_level=2,
            liked_ingredients=[" GÀ ", "rau", "gà"],
            avoided_ingredients=[" LẠC ", "tôm"],
            exploration_level=2,
        )
    )
    db.commit()
    db.expire_all()

    stored = db.get(Preference, 1)
    assert stored.user.email == "customer1@example.vn"
    assert stored.regions == ["Bắc", "Nam"]
    assert stored.spice_level == 2
    assert stored.liked_ingredients == ["gà", "rau"]
    assert stored.avoided_ingredients == ["lạc", "tôm"]
    assert stored.exploration_level == 2


def test_skip_is_represented_by_no_profile(db):
    assert db.get(User, 1) is not None
    assert db.get(Preference, 1) is None


def test_each_user_can_only_have_one_profile(db):
    db.add(Preference(user_id=1))
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(text("INSERT INTO preferences (user_id) VALUES (1)"))
    db.rollback()
    assert db.query(Preference).filter_by(user_id=1).count() == 1


def test_profile_cannot_reference_missing_user(db):
    db.add(Preference(user_id=999))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_deleting_account_removes_its_profile(db):
    db.add(Preference(user_id=1))
    db.commit()
    db.execute(text("DELETE FROM users WHERE id = 1"))
    db.commit()
    assert db.get(Preference, 1) is None


def test_default_lists_are_independent_between_accounts(db):
    first = Preference(user_id=1)
    second = Preference(user_id=2)
    db.add_all([first, second])
    db.flush()
    first.avoided_ingredients.append("lạc")
    db.commit()
    db.expire_all()
    assert db.get(Preference, 1).avoided_ingredients == ["lạc"]
    assert db.get(Preference, 2).avoided_ingredients == []


@pytest.mark.parametrize(
    "field,choice",
    [("regions", "Bắc"), ("liked_ingredients", "gà"), ("avoided_ingredients", "lạc")],
)
def test_in_place_list_changes_are_persisted(db, field, choice):
    db.add(Preference(user_id=1))
    db.commit()
    preference = db.get(Preference, 1)
    getattr(preference, field).append(choice)
    db.commit()
    db.expire_all()
    assert getattr(db.get(Preference, 1), field) == [choice]
    getattr(db.get(Preference, 1), field).remove(choice)
    db.commit()
    db.expire_all()
    assert getattr(db.get(Preference, 1), field) == []


@pytest.mark.parametrize("field,maximum", [("spice_level", 3), ("exploration_level", 2)])
@pytest.mark.parametrize("invalid", [-1, "1", True, 1.5])
def test_invalid_levels_are_rejected_before_persistence(field, maximum, invalid):
    with pytest.raises(ValueError):
        Preference(user_id=1, **{field: invalid})
    with pytest.raises(ValueError):
        Preference(user_id=1, **{field: maximum + 1})


@pytest.mark.parametrize(
    "field,invalid",
    [("spice_level", -1), ("spice_level", 4), ("exploration_level", -1), ("exploration_level", 3)],
)
def test_database_also_enforces_level_ranges(db, field, invalid):
    # field lấy từ tập hằng số của kiểm thử; giá trị đầu vào vẫn được bind riêng.
    with pytest.raises(IntegrityError):
        db.execute(
            text(f"INSERT INTO preferences (user_id, {field}) VALUES (1, :value)"),
            {"value": invalid},
        )
    db.rollback()


@pytest.mark.parametrize("field", ["regions", "liked_ingredients", "avoided_ingredients"])
@pytest.mark.parametrize("invalid", [None, "gà", [1], ["   "]])
def test_answers_require_lists_of_nonempty_strings(field, invalid):
    with pytest.raises(ValueError):
        Preference(user_id=1, **{field: invalid})


def test_database_defaults_apply_to_raw_inserts(db):
    db.execute(text("INSERT INTO preferences (user_id) VALUES (1)"))
    db.commit()
    stored = db.get(Preference, 1)
    assert stored.regions == stored.liked_ingredients == stored.avoided_ingredients == []
    assert stored.spice_level == 0
    assert stored.exploration_level == 1
