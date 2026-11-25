from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from supabase import Client

from src.backend.api.dependencies import get_db, require_admin
from src.backend.api.schemas.report import ReportCreate, ReportDTO, ReportUpdateStatus
from src.backend.api.services import report_service

router = APIRouter(prefix="/api", tags=["Reports"])


@router.post("/reports", response_model=ReportDTO, status_code=status.HTTP_201_CREATED)
def submit_report(payload: ReportCreate, db: Client = Depends(get_db)):
    """Người dùng gửi báo cáo tin đăng sai sự thật hoặc lừa đảo."""
    return report_service.create_report(db=db, payload=payload)


@router.get("/admin/reports", response_model=List[ReportDTO])
def list_admin_reports(
    status_filter: Optional[str] = Query(None, alias="status"),
    _admin: Dict[str, Any] = Depends(require_admin),
    db: Client = Depends(get_db),
):
    """Quản trị viên xem danh sách báo cáo vi phạm."""
    return report_service.list_reports(db=db, status_filter=status_filter)


@router.patch("/admin/reports/{report_id}", response_model=ReportDTO)
def review_report(
    report_id: int,
    payload: ReportUpdateStatus,
    _admin: Dict[str, Any] = Depends(require_admin),
    db: Client = Depends(get_db),
):
    """Quản trị viên duyệt xử lý báo cáo vi phạm."""
    return report_service.update_report_status(db=db, report_id=report_id, payload=payload)
