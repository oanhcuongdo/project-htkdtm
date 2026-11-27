"""Shared API schema primitives, camelCase serialization, and standard envelopes."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Base schema with automatic camelCase JSON serialization."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class PageMeta(ApiModel):
    """Pagination metadata matching frontend PageMeta contract."""

    page: int
    page_size: int
    total: int
    total_pages: int


class Envelope[T](ApiModel):
    """Standard success response wrapper: {data, meta}."""

    data: T
    meta: PageMeta | None = None
