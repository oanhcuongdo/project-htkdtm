from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator


class ModelEvaluationMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(min_length=1, max_length=64)
    model_version: str = Field(min_length=1, max_length=255)
    profile_count: StrictInt = Field(ge=1)
    labeled_pair_count: StrictInt = Field(ge=0)
    course_count: StrictInt = Field(ge=1)
    ndcg_at_5: float = Field(ge=0, le=1, allow_inf_nan=False)
    precision_at_5: float = Field(ge=0, le=1, allow_inf_nan=False)
    prerequisite_violations: StrictInt = Field(ge=0)
    profiles_under_5_results: StrictInt = Field(ge=0)
    p50_latency_ms: float = Field(ge=0, allow_inf_nan=False)
    p95_latency_ms: float = Field(ge=0, allow_inf_nan=False)
    relative_ndcg_gain_vs_m0: float | None = Field(
        default=None,
        allow_inf_nan=False,
    )
    goal_status: dict[str, bool | None]
    evaluation_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("model_name", "model_version")
    @classmethod
    def reject_blank_identifiers(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("model identifiers must not be blank")
        return value

    @field_validator("p50_latency_ms", "p95_latency_ms", mode="before")
    @classmethod
    def reject_boolean_latency(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("latency must be a finite non-negative number")
        return value

    @field_validator("ndcg_at_5", "precision_at_5", "relative_ndcg_gain_vs_m0", mode="before")
    @classmethod
    def reject_boolean_metric(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("metrics must be finite numbers")
        return value

    @model_validator(mode="after")
    def validate_profile_count(self) -> "ModelEvaluationMetric":
        if self.profiles_under_5_results > self.profile_count:
            raise ValueError("profiles_under_5_results cannot exceed profile_count")
        return self


class ModelEvaluationBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: StrictInt
    evaluation_batch_id: UUID
    created_at: datetime
    dataset_version_id: str = Field(min_length=1, max_length=128)
    evaluation_split: Literal["test"]
    top_k: StrictInt = Field(ge=1)
    course_count: StrictInt = Field(ge=1)
    profile_count: StrictInt = Field(ge=1)
    labeled_pair_count: StrictInt = Field(ge=0)
    evaluation_metadata: dict[str, Any]
    metrics: list[ModelEvaluationMetric] = Field(min_length=1)

    @field_validator("schema_version")
    @classmethod
    def require_supported_schema(cls, value: int) -> int:
        if value != 1:
            raise ValueError("schema_version must equal 1")
        return value

    @field_validator("dataset_version_id")
    @classmethod
    def reject_blank_version(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("dataset_version_id must not be blank")
        return value

    @field_validator("created_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_batch(self) -> "ModelEvaluationBatch":
        if self.top_k != 5:
            raise ValueError("evaluation batch must contain top_k=5 metrics")
        names = [metric.model_name for metric in self.metrics]
        if len(names) != len(set(names)):
            raise ValueError("model_name values must be unique within a batch")
        for metric in self.metrics:
            if (
                metric.profile_count != self.profile_count
                or metric.labeled_pair_count != self.labeled_pair_count
                or metric.course_count != self.course_count
            ):
                raise ValueError("metric counts must match the evaluation batch")
        return self


class ModelEvaluationBatchReceipt(BaseModel):
    evaluation_batch_id: UUID
    batch_sha256: str
    model_count: int
    dataset_version_id: str
    evaluation_split: str
    created_at: datetime
