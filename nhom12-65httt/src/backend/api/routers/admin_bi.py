from typing import Any, Dict
from fastapi import APIRouter, Depends, Query
from supabase import Client

from src.backend.api.dependencies import get_db, require_admin
from src.backend.api.schemas.admin_bi import AnomalyListResponse, AnomalyRecalculateResponse
from src.backend.api.services import anomaly_service

router = APIRouter(prefix="/api/admin", tags=["Admin BI & Anomaly"])


@router.get("/anomalies", response_model=AnomalyListResponse)
def get_market_anomalies(
    min_risk_score: float = Query(25.0, ge=0.0, le=100.0, description="Ngưỡng điểm rủi ro tối thiểu"),
    limit: int = Query(50, ge=1, le=200),
    _admin: Dict[str, Any] = Depends(require_admin),
    db: Client = Depends(get_db),
):
    """Quản trị viên xem danh sách tin đăng có dấu hiệu bất thường / rủi ro tin ảo."""
    return anomaly_service.list_market_anomalies(db=db, min_risk_score=min_risk_score, limit=limit)


@router.post("/anomalies/recalculate", response_model=AnomalyRecalculateResponse)
def recalculate_anomalies(
    _admin: Dict[str, Any] = Depends(require_admin),
    db: Client = Depends(get_db),
):
    """Quản trị viên kích hoạt rà soát và tính lại điểm rủi ro, độ đầy đủ và chênh lệch giá."""
    return anomaly_service.recalculate_market_anomalies(db=db)
