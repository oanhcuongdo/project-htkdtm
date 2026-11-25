from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.security import decrypt_config, encrypt_config, get_current_user

router = APIRouter(prefix="/api/v1/sources", tags=["User Data Sources Configuration"])

DEFAULT_SOURCES = [
    {
        "source_type": "CSV_UPLOAD",
        "display_name": "Tải lên Sao kê Ngân hàng (Excel / CSV / PDF)",
        "description": "Kéo-thả trực tiếp file sao kê tải từ MB Bank, Vietcombank, Techcombank, MoMo.",
    },
    {
        "source_type": "EMAIL_IMAP",
        "display_name": "Đồng bộ tự động Email biến động số dư (IMAP)",
        "description": "Đọc một chiều (Read-only) email thông báo giao dịch mỗi 15 phút, mã hóa App Password.",
    },
    {
        "source_type": "TELEGRAM_OCR",
        "display_name": "Quét ảnh Hóa đơn / Biên lai (Telegram + OCR)",
        "description": "Gửi ảnh hóa đơn hoặc tải ảnh biên lai để Tesseract OCR bóc tách số tiền tự động.",
    },
]


class SourceConfigRequest(BaseModel):
    source_type: str  # CSV_UPLOAD | EMAIL_IMAP | TELEGRAM_OCR
    is_enabled: bool = True
    imap_server: Optional[str] = "imap.gmail.com"
    imap_email: Optional[str] = None
    imap_app_password: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    preferred_banks: Optional[str] = "MBBank, VCB, MoMo"


@router.get("")
def list_user_data_sources(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lấy danh sách các phương thức lấy dữ liệu ngân hàng và trạng thái cấu hình của user."""
    uid = current_user["user_id"]
    rows = db.execute(
        text("""
            SELECT source_id, source_type, display_name, config_encrypted, is_enabled, last_sync_at
            FROM user_data_sources
            WHERE user_id = :uid
        """),
        {"uid": uid},
    ).mappings().all()

    saved_map = {r["source_type"]: dict(r) for r in rows}

    # Thống kê số giao dịch đã nạp theo kênh của user này
    counts_rows = db.execute(
        text("""
            SELECT source_type, COUNT(*) AS cnt
            FROM fact_transactions
            WHERE user_id = :uid
            GROUP BY source_type
        """),
        {"uid": uid},
    ).fetchall()
    tx_by_source = {r[0]: int(r[1]) for r in counts_rows}

    result = []
    for default in DEFAULT_SOURCES:
        stype = default["source_type"]
        saved = saved_map.get(stype)
        cfg = decrypt_config(saved["config_encrypted"]) if saved else {}

        # Che mật khẩu ứng dụng khi trả ra frontend
        safe_cfg = {k: ("••••••••" if "password" in k and v else v) for k, v in cfg.items()}

        ingested_cnt = (
            tx_by_source.get("CSV", 0) + tx_by_source.get("PDF", 0)
            if stype == "CSV_UPLOAD"
            else tx_by_source.get("EMAIL", 0)
            if stype == "EMAIL_IMAP"
            else tx_by_source.get("TELEGRAM", 0)
        )

        result.append(
            {
                "source_type": stype,
                "display_name": default["display_name"],
                "description": default["description"],
                "is_enabled": bool(saved["is_enabled"]) if saved else (stype == "CSV_UPLOAD"),
                "is_configured": bool(saved),
                "last_sync_at": saved["last_sync_at"].isoformat() if saved and saved["last_sync_at"] else None,
                "transactions_ingested": ingested_cnt,
                "config_masked": safe_cfg,
            }
        )

    return {"user_id": uid, "sources": result}


@router.post("/configure")
def configure_data_source(
    payload: SourceConfigRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lưu cấu hình phương thức thu thập dữ liệu ngân hàng cá nhân (mã hóa Fernet các trường nhạy cảm)."""
    valid_types = {d["source_type"]: d["display_name"] for d in DEFAULT_SOURCES}
    if payload.source_type not in valid_types:
        raise HTTPException(status_code=400, detail="Loại nguồn dữ liệu không hợp lệ.")

    uid = current_user["user_id"]
    cfg = {}
    if payload.source_type == "EMAIL_IMAP":
        cfg = {
            "imap_server": payload.imap_server or "imap.gmail.com",
            "imap_email": payload.imap_email or "",
            "imap_app_password": payload.imap_app_password or "",
        }
    elif payload.source_type == "TELEGRAM_OCR":
        cfg = {"telegram_chat_id": payload.telegram_chat_id or ""}
    else:
        cfg = {"preferred_banks": payload.preferred_banks or "MBBank, VCB, MoMo"}

    encrypted = encrypt_config(cfg)

    db.execute(
        text("""
            INSERT INTO user_data_sources (user_id, source_type, display_name, config_encrypted, is_enabled, last_sync_at)
            VALUES (:uid, :stype, :dname, :cfg, :enabled, :now)
            ON CONFLICT (user_id, source_type) DO UPDATE
            SET config_encrypted = EXCLUDED.config_encrypted,
                is_enabled = EXCLUDED.is_enabled,
                last_sync_at = EXCLUDED.last_sync_at
        """),
        {
            "uid": uid,
            "stype": payload.source_type,
            "dname": valid_types[payload.source_type],
            "cfg": encrypted,
            "enabled": payload.is_enabled,
            "now": datetime.now(),
        },
    )
    db.commit()

    return {
        "status": "saved",
        "source_type": payload.source_type,
        "is_enabled": payload.is_enabled,
        "message": f"Đã lưu cấu hình kênh '{valid_types[payload.source_type]}' an toàn (đã mã hóa).",
    }
