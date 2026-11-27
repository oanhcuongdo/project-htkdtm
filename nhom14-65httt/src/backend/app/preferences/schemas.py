"""Năm câu trả lời khẩu vị của khách hàng."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

Choice = Annotated[str, Field(min_length=1, max_length=100)]
SpiceLevel = Annotated[int, Field(strict=True, ge=0, le=3)]
ExplorationLevel = Annotated[int, Field(strict=True, ge=0, le=2)]


class PreferenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    regions: list[Choice] = Field(max_length=100)
    spice_level: SpiceLevel
    liked_ingredients: list[Choice] = Field(max_length=100)
    avoided_ingredients: list[Choice] = Field(max_length=100)
    exploration_level: ExplorationLevel

    @field_validator("regions", "liked_ingredients", "avoided_ingredients", mode="before")
    @classmethod
    def clean_choices(cls, value, info):
        if not isinstance(value, list) or len(value) > 100:
            raise ValueError("Câu trả lời phải là danh sách tối đa 100 chuỗi.")
        choices, seen = [], set()
        for entry in value:
            if not isinstance(entry, str) or not entry.strip():
                raise ValueError("Câu trả lời không nhận chuỗi rỗng hoặc giá trị khác chuỗi.")
            cleaned = entry.strip() if info.field_name == "regions" else entry.strip().lower()
            if cleaned.casefold() not in seen:
                choices.append(cleaned)
                seen.add(cleaned.casefold())
        return choices


class PreferenceOut(PreferenceInput):
    model_config = ConfigDict(from_attributes=True)
