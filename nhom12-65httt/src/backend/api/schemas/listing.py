from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ListingCardDTO(BaseModel):
    fact_id: str
    source: str
    external_id: str
    title: str
    original_url: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    videos: List[Any] = Field(default_factory=list)
    price: float
    original_price: Optional[float] = None
    area: Optional[float] = None
    price_per_m2: Optional[float] = None
    estimated_total_cost: Optional[float] = None
    price_diff_rate: float = 0.0
    price_segment: str = "trung_cap"
    risk_score: float = 0.0
    completeness_score: float = 0.0
    is_active: bool = True
    is_promoted: bool = False
    room_status: str = "con_trong"
    view_count: int = 0
    wishlist_count: int = 0
    district: str = ""
    ward: str = ""
    street: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    nearest_university: Optional[str] = None
    distance_to_university_km: Optional[float] = None
    distance_to_target_km: Optional[float] = None
    type_code: str = "phong_tro"
    type_name: str = "Phòng trọ / Nhà trọ"
    poster_name: str = "Chính chủ"
    poster_type: str = "unknown"
    landlord_trust_score: float = 5.0
    is_verified_seller: bool = False
    has_air_conditioner: bool = False
    has_water_heater: bool = False
    has_washing_machine: bool = False
    has_private_bathroom: bool = False
    has_elevator: bool = False
    has_flexible_hours: bool = False
    created_at: Optional[str] = None


class ListingDetailDTO(ListingCardDTO):
    description: Optional[str] = None
    deposit_amount: float = 0.0
    electricity_cost: Optional[float] = None
    water_cost: Optional[float] = None
    service_cost: float = 0.0
    extraction_source: str = "regex"
    orig_published_at: Optional[str] = None
    last_bumped_at: Optional[str] = None
    closed_at: Optional[str] = None
    days_on_market: Optional[float] = None
    phone_masked: Optional[str] = None
    sold_ads_count: int = 0
    has_refrigerator: bool = False
    has_kitchen: bool = False
    has_balcony: bool = False
    has_parking: bool = False
    has_security: bool = False
    has_mezzanine: bool = False
    raw_amenities: List[str] = Field(default_factory=list)


class ListingListResponse(BaseModel):
    items: List[ListingCardDTO]
    total: int
    page: int
    limit: int
    total_pages: int


class CompareResponse(BaseModel):
    items: List[ListingDetailDTO]


class DistrictStatDTO(BaseModel):
    district: str
    listing_count: int
    avg_price: float
    avg_price_per_m2: Optional[float] = None
    min_price: float
    max_price: float
    avg_risk_score: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
