from typing import List, Optional
from pydantic import BaseModel


class AnomalyListingDTO(BaseModel):
    fact_id: str
    title: str
    district: Optional[str] = None
    type_name: Optional[str] = None
    price: float
    area: Optional[float] = None
    price_per_m2: Optional[float] = None
    price_diff_rate: float = 0.0
    completeness_score: float = 0.0
    risk_score: float = 0.0
    risk_level: str
    risk_flags: List[str] = []
    report_count: int = 0
    is_active: bool = True
    original_url: Optional[str] = None


class AnomalySummaryDTO(BaseModel):
    total_listings: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    avg_completeness_score: float
    avg_risk_score: float


class AnomalyListResponse(BaseModel):
    summary: AnomalySummaryDTO
    items: List[AnomalyListingDTO]


class AnomalyRecalculateResponse(BaseModel):
    updated_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    avg_completeness_score: float
    message: str
