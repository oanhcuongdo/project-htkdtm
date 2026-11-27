from fastapi import APIRouter, Depends
from supabase import Client

from src.backend.api.dependencies import get_db
from src.backend.api.schemas.bi import MarketBIOverviewResponse
from src.backend.api.services.bi_service import get_market_bi_overview

router = APIRouter(prefix="/api/bi", tags=["Market BI Analytics"])


@router.get("/overview", response_model=MarketBIOverviewResponse)
def get_bi_overview(db: Client = Depends(get_db)):
    """Lấy dữ liệu tổng hợp 3 nhóm Insight thị trường cho trang Analytics BI."""
    return get_market_bi_overview(db=db)
