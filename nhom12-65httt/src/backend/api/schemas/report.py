from typing import Literal, Optional
from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    fact_id: str
    reporter_session_id: Optional[str] = None
    reason: str = Field(min_length=3, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)


class ReportUpdateStatus(BaseModel):
    status: Literal["pending", "reviewed", "resolved", "dismissed"]
    deactivate_listing: bool = False


class ReportDTO(BaseModel):
    report_id: int
    fact_id: str
    listing_title: Optional[str] = None
    listing_url: Optional[str] = None
    reporter_session_id: Optional[str] = None
    reason: str
    description: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    reviewed_at: Optional[str] = None
