from fastapi import FastAPI, Query
from typing import Optional, List
from src.backend.database.supabase_client import get_supabase_client

app = FastAPI(
    title="Smart Rental Housing API",
    description="Backend API cho Hệ thống tìm kiếm nhà thuê thông minh (Hà Nội) - Nhóm 12 (65HTTT)",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "project": "Hệ Thống Tìm Kiếm Nhà Thuê Thông Minh",
        "group": "Nhóm 12 - 65HTTT",
        "status": "online"
    }

@app.get("/api/listings")
def get_listings(
    district: Optional[str] = Query(None, description="Lọc theo Quận/Huyện"),
    min_price: Optional[float] = Query(None, description="Giá thuê tối thiểu"),
    max_price: Optional[float] = Query(None, description="Giá thuê tối đa"),
    limit: int = Query(20, ge=1, le=100)
):
    """Lấy danh sách phòng trọ từ view view_rental_market_analytics."""
    client = get_supabase_client()
    query = client.table("view_rental_market_analytics").select("*")
    if district:
        query = query.ilike("district", f"%{district}%")
    if min_price is not None:
        query = query.gte("price", min_price)
    if max_price is not None:
        query = query.lte("price", max_price)
    
    res = query.limit(limit).execute()
    return {"total": len(res.data), "data": res.data}
