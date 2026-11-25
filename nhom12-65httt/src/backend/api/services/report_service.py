import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from supabase import Client

from src.backend.api.dependencies import validate_uuid
from src.backend.api.schemas.report import ReportCreate, ReportDTO, ReportUpdateStatus


def create_report(db: Client, payload: ReportCreate) -> ReportDTO:
    """Lưu báo cáo tin sai sự thật vào listing_reports."""
    clean_fact_id = validate_uuid(payload.fact_id, "fact_id")
    exists = (
        db.table("fact_rental_listings")
        .select("fact_id")
        .eq("fact_id", clean_fact_id)
        .limit(1)
        .execute()
    )
    if not exists.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phòng trọ cần báo cáo.")

    row = {
        "fact_id": clean_fact_id,
        "reporter_session_id": payload.reporter_session_id,
        "reason": payload.reason,
        "description": payload.description,
        "status": "pending",
    }
    res = db.table("listing_reports").insert(row).execute()
    created = res.data[0]
    return ReportDTO(
        report_id=created["report_id"],
        fact_id=str(created["fact_id"]),
        reporter_session_id=created.get("reporter_session_id"),
        reason=created["reason"],
        description=created.get("description"),
        status=created["status"],
        created_at=str(created["created_at"]) if created.get("created_at") else None,
    )


def list_reports(db: Client, status_filter: Optional[str] = None) -> List[ReportDTO]:
    """Lấy danh sách báo cáo vi phạm (dành cho Quản trị viên)."""
    query = (
        db.table("listing_reports")
        .select("*, fact_rental_listings(title, original_url)")
        .order("created_at", desc=True)
    )
    if status_filter:
        query = query.eq("status", status_filter)
    rows = query.execute().data or []

    results: List[ReportDTO] = []
    for r in rows:
        fact = r.get("fact_rental_listings") or {}
        results.append(
            ReportDTO(
                report_id=r["report_id"],
                fact_id=str(r["fact_id"]),
                listing_title=fact.get("title"),
                listing_url=fact.get("original_url"),
                reporter_session_id=r.get("reporter_session_id"),
                reason=r["reason"],
                description=r.get("description"),
                status=r["status"],
                created_at=str(r["created_at"]) if r.get("created_at") else None,
                reviewed_at=str(r["reviewed_at"]) if r.get("reviewed_at") else None,
            )
        )
    return results


def update_report_status(db: Client, report_id: int, payload: ReportUpdateStatus) -> ReportDTO:
    """Cập nhật trạng thái xử lý báo cáo (và ẩn tin vi phạm nếu Admin chọn)."""
    existing = (
        db.table("listing_reports")
        .select("*")
        .eq("report_id", report_id)
        .limit(1)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy báo cáo.")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    res = (
        db.table("listing_reports")
        .update({"status": payload.status, "reviewed_at": now_iso})
        .eq("report_id", report_id)
        .execute()
    )
    updated = res.data[0]

    if payload.status == "resolved" and payload.deactivate_listing:
        db.table("fact_rental_listings").update({
            "is_active": False,
            "room_status": "het_han",
            "closed_at": now_iso,
        }).eq("fact_id", updated["fact_id"]).execute()

    return ReportDTO(
        report_id=updated["report_id"],
        fact_id=str(updated["fact_id"]),
        reporter_session_id=updated.get("reporter_session_id"),
        reason=updated["reason"],
        description=updated.get("description"),
        status=updated["status"],
        created_at=str(updated["created_at"]) if updated.get("created_at") else None,
        reviewed_at=str(updated["reviewed_at"]) if updated.get("reviewed_at") else None,
    )
