from datetime import datetime
import math
from typing import Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
    model_validator,
)


class RecommendationItemTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    course_id: str = Field(min_length=1, max_length=255)
    rank: StrictInt = Field(ge=1)
    score: float | None = Field(default=None, allow_inf_nan=False)
    score_scale: str = Field(min_length=1, max_length=32)
    ranking_method: str = Field(min_length=1, max_length=64)
    fallback_reason: str | None = None
    score_components: dict[str, float | None] | None = None
    score_metadata: dict[str, Any] | None = None
    course_snapshot: dict[str, Any]
    explanation: dict[str, Any]

    @field_validator("course_id", "score_scale", "ranking_method")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value

    @field_validator("score", mode="before")
    @classmethod
    def reject_boolean_score(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("score must be a finite number or null")
        return value

    @field_validator("score_components", mode="before")
    @classmethod
    def validate_score_components(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, dict):
            for name, component in value.items():
                if not isinstance(name, str) or not name.strip():
                    raise ValueError("score component names must not be blank")
                if component is not None and (
                    isinstance(component, bool)
                    or not isinstance(component, (int, float))
                    or not math.isfinite(component)
                ):
                    raise ValueError("score components must be finite numbers or null")
        return value


class RecommendationRunTrace(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    request_id: UUID
    student_id: UUID | None = None
    learner_key: str | None = Field(default=None, min_length=1, max_length=128)
    model_name: Literal["M0", "M1", "M2"]
    model_version: str = Field(min_length=1, max_length=255)
    dataset_version_id: str = Field(min_length=1, max_length=128)
    created_at: datetime
    candidate_set_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    top_k: StrictInt = Field(ge=1)
    model_settings: dict[str, Any] = Field(alias="model_config")
    input_snapshot: dict[str, Any]
    filter_snapshot: dict[str, Any]
    items: list[RecommendationItemTrace]

    @field_validator("model_version", "dataset_version_id")
    @classmethod
    def reject_blank_identifiers(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value

    @field_validator("created_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_trace_integrity(self) -> "RecommendationRunTrace":
        if (self.student_id is None) == (self.learner_key is None):
            raise ValueError("exactly one of student_id or learner_key is required")
        if self.learner_key is not None and not self.learner_key.strip():
            raise ValueError("learner_key must not be blank")
        ranks = [item.rank for item in self.items]
        course_ids = [item.course_id for item in self.items]
        if len(ranks) != len(set(ranks)):
            raise ValueError("recommendation item ranks must be unique")
        if len(course_ids) != len(set(course_ids)):
            raise ValueError("recommendation item course IDs must be unique")
        if any(rank > self.top_k for rank in ranks):
            raise ValueError("recommendation item rank must not exceed top_k")
        return self


class RecommendationRunReceipt(BaseModel):
    id: UUID
    request_id: UUID
    model_name: str
    model_version: str
    dataset_version_id: str
    candidate_set_hash: str
    trace_sha256: str
    item_count: int
    created_at: datetime
