from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from supabase import Client

from src.backend.api.dependencies import get_db
from src.backend.api.schemas.listing import (
    CompareResponse,
    DistrictStatDTO,
    ListingDetailDTO,
    ListingListResponse,
)
from src.backend.api.services import listing_service

router = APIRouter(prefix="/api/listings", tags=["Listings"])


@router.get("", response_model=ListingListResponse)
def get_listings(
    q: Optional[str] = Query(None, description="Từ khóa tiêu đề hoặc địa chỉ"),
    district: Optional[str] = Query(None, description="Lọc theo Quận/Huyện"),
    ward: Optional[str] = Query(None, description="Lọc theo Phường/Xã"),
    property_type: Optional[str] = Query(None, description="Mã loại hình (phong_tro, chung_cu_mini...)"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_area: Optional[float] = Query(None, ge=0),
    max_area: Optional[float] = Query(None, ge=0),
    amenities: Optional[str] = Query(None, description="Danh sách tiện ích cách nhau bởi dấu phẩy"),
    lat: Optional[float] = Query(None, description="Vĩ độ tâm tìm kiếm"),
    lon: Optional[float] = Query(None, description="Kinh độ tâm tìm kiếm"),
    radius_km: Optional[float] = Query(None, gt=0, le=50, description="Bán kính Haversine (km)"),
    sort_by: str = Query(
        "newest",
        pattern="^(newest|price_asc|price_desc|total_cost_asc|price_per_m2_asc|trust_desc|distance_asc)$",
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Client = Depends(get_db),
):
    """Lấy danh sách phòng trọ hợp lệ có lọc đa tiêu chí, bán kính và phân trang."""
    return listing_service.list_listings(
        db=db,
        q=q,
        district=district,
        ward=ward,
        property_type=property_type,
        min_price=min_price,
        max_price=max_price,
        min_area=min_area,
        max_area=max_area,
        amenities=amenities,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        sort_by=sort_by,
        page=page,
        limit=limit,
    )


@router.get("/compare", response_model=CompareResponse)
def compare_listings(
    ids: str = Query(..., description="Danh sách 2-3 fact_id cách nhau bởi dấu phẩy"),
    db: Client = Depends(get_db),
):
    """So sánh chi tiết 2–3 phòng trọ."""
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    return listing_service.compare_listings(db=db, ids=id_list)


@router.get("/stats/districts", response_model=List[DistrictStatDTO])
def get_district_stats(db: Client = Depends(get_db)):
    """Thống kê mặt bằng giá thuê và nguồn cung theo từng quận/huyện."""
    return listing_service.get_district_stats(db=db)


@router.get("/{fact_id}", response_model=ListingDetailDTO)
def get_listing_detail(fact_id: str, db: Client = Depends(get_db)):
    """Lấy thông tin chi tiết đầy đủ của một phòng trọ."""
    return listing_service.get_listing_detail(db=db, fact_id=fact_id)
