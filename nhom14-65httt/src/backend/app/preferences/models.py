"""Lưu năm câu trả lời khẩu vị; mỗi người dùng có tối đa một hồ sơ."""

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Integer, text
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.database import Base
from app.users.models import User


class Preference(Base):
    __tablename__ = "preferences"
    __table_args__ = (
        CheckConstraint("spice_level BETWEEN 0 AND 3", name="ck_preferences_spice_level"),
        CheckConstraint(
            "exploration_level BETWEEN 0 AND 2", name="ck_preferences_exploration_level"
        ),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    regions: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON(none_as_null=True)),
        nullable=False,
        default=list,
        server_default=text("'[]'"),
    )
    spice_level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    liked_ingredients: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON(none_as_null=True)),
        nullable=False,
        default=list,
        server_default=text("'[]'"),
    )
    avoided_ingredients: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON(none_as_null=True)),
        nullable=False,
        default=list,
        server_default=text("'[]'"),
    )
    exploration_level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )

    user: Mapped[User] = relationship()

    @validates("regions", "liked_ingredients", "avoided_ingredients")
    def normalize_choices(self, key: str, value: list[str]) -> list[str]:
        if not isinstance(value, list):
            raise ValueError(f"{key} phải là danh sách chuỗi.")
        choices = []
        seen = set()
        for choice in value:
            if not isinstance(choice, str) or not choice.strip():
                raise ValueError(f"{key} không nhận phần tử rỗng hoặc khác kiểu chuỗi.")
            normalized = choice.strip()
            if key != "regions":
                normalized = normalized.lower()
            identifier = normalized.casefold()
            if identifier not in seen:
                seen.add(identifier)
                choices.append(normalized)
        return choices

    @validates("spice_level", "exploration_level")
    def validate_level(self, key: str, value: int) -> int:
        maximum = 3 if key == "spice_level" else 2
        if type(value) is not int or not 0 <= value <= maximum:
            raise ValueError(f"{key} phải là số nguyên từ 0 đến {maximum}.")
        return value
