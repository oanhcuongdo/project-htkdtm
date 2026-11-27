from typing import List, Optional
from pydantic import BaseModel


class DistrictPriceStat(BaseModel):
    district: str
    avg_price: float
    avg_price_per_m2: float
    listing_count: int


class PropertyTypeStat(BaseModel):
    type_name: str
    avg_price: float
    avg_price_per_m2: float
    listing_count: int


class PriceSegmentStat(BaseModel):
    segment: str
    label: str
    listing_count: int


class MonthlyTrendStat(BaseModel):
    period: str
    avg_price_per_m2: float
    avg_price: float
    listing_count: int


class LiquidityDistrictStat(BaseModel):
    district: str
    avg_days_on_market: float
    active_count: int
    closed_count: int


class MarketBIOverviewResponse(BaseModel):
    total_active_listings: int
    total_districts: int
    avg_price: float
    avg_price_per_m2: float
    avg_days_on_market: Optional[float] = None
    price_by_district: List[DistrictPriceStat]
    price_by_property_type: List[PropertyTypeStat]
    supply_by_segment: List[PriceSegmentStat]
    trend_by_month: List[MonthlyTrendStat]
    liquidity_by_district: List[LiquidityDistrictStat]
