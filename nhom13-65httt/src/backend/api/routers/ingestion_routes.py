import os
import tempfile
from datetime import datetime
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.dependencies import get_db
from etl_pipeline.data_quality import DataQualityChecker
from etl_pipeline.pipeline_runner import ETLPipelineRunner
from ingestion.email_collector.imap_client import IMAPEmailCollector
from ingestion.statement_parser import StatementPDFParser, StatementTabularParser
from ingestion.telegram_bot.bot import FinanceTelegramBot
from ingestion.telegram_bot.ocr_engine import ReceiptOCREngine
from scheduler.cron_jobs import scan_watch_folder

router = APIRouter(prefix="/api/v1/ingestion", tags=["Data Ingestion & ETL Pipeline"])


class EmailIngestRequest(BaseModel):
    message_id: str
    sender: str
    subject: str
    body_text: str


class ReceiptTextRequest(BaseModel):
    ocr_text: str
    chat_id: int = 0


@router.post("/upload-statement")
async def upload_statement(file: UploadFile = File(...)):
    """Tải lên file sao kê (.xlsx, .xls, .csv, .pdf), bóc tách vào Staging, khử trùng lặp và nạp vào Data Warehouse."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".xlsx", ".xls", ".csv", ".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file sao kê định dạng .xlsx, .xls, .csv, .pdf")

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        if ext == ".pdf":
            dtos = StatementPDFParser().parse_file(tmp_path)
        else:
            dtos = StatementTabularParser().parse_file(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    if not dtos:
        return {"file_name": file.filename, "status": "empty", "message": "Không trích xuất được giao dịch hợp lệ từ file."}

    summary = ETLPipelineRunner().run(dtos, pipeline_name=f"Upload_{file.filename}")
    return {"file_name": file.filename, "etl_summary": summary}


@router.post("/ingest-email")
def ingest_email_sample(payload: EmailIngestRequest):
    """Nhận nội dung email biến động số dư, lưu Staging, bóc tách và nạp vào Kho dữ liệu."""
    collector = IMAPEmailCollector()
    dtos = collector.process_raw_emails([
        (payload.message_id, payload.sender, payload.subject, "", payload.body_text, datetime.now())
    ])
    if not dtos:
        return {"status": "failed", "message": "Email không khớp định dạng ngân hàng được hỗ trợ (VCB, MBBank, Techcombank, MoMo)."}

    summary = ETLPipelineRunner().run(dtos, pipeline_name="API_Email_Ingest")
    return {"status": "success", "etl_summary": summary}


@router.post("/ingest-receipt-image")
async def ingest_receipt_image(file: UploadFile = File(...), chat_id: int = 0):
    """Nhận ảnh hóa đơn/biên lai, chạy Tesseract OCR tiếng Việt và nạp vào Kho dữ liệu."""
    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        bot = FinanceTelegramBot()
        return bot.handle_receipt_image(file_id=file.filename or "api_upload", chat_id=chat_id, local_image_path=tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/ingest-receipt-text")
def ingest_receipt_text(payload: ReceiptTextRequest):
    """Kiểm thử bóc tách văn bản biên lai OCR và nạp vào Kho dữ liệu."""
    dto = ReceiptOCREngine().parse_receipt_text(payload.ocr_text, chat_id=payload.chat_id)
    if not dto:
        return {"status": "failed", "message": "Không trích xuất được số tiền hợp lệ từ văn bản biên lai."}
    summary = ETLPipelineRunner().run([dto], pipeline_name="API_Receipt_Text_Ingest")
    return {"status": "success", "etl_summary": summary}


@router.post("/scan-watch-folder")
def trigger_watch_folder_scan(force_rescan: bool = False):
    """Quét thủ công thư mục watch_statements (chứa các file sao kê như SAO_KE_TAI_KHOAN_1.xlsx)."""
    return scan_watch_folder(force_rescan=force_rescan)


@router.get("/logs")
def get_ingestion_and_dedup_logs(db: Session = Depends(get_db)):
    """Lấy thống kê tổng quan kho dữ liệu, nhật ký chạy pipeline và nhật ký khử trùng lặp."""
    fact_count = db.execute(text("SELECT COUNT(*) FROM fact_transactions")).scalar() or 0
    stg_email_cnt = db.execute(text("SELECT COUNT(*) FROM stg_raw_emails")).scalar() or 0
    stg_stmt_cnt = db.execute(text("SELECT COUNT(*) FROM stg_raw_statements")).scalar() or 0
    stg_rcpt_cnt = db.execute(text("SELECT COUNT(*) FROM stg_raw_receipts")).scalar() or 0
    dedup_cnt = db.execute(text("SELECT COUNT(*) FROM log_dedup")).scalar() or 0

    pipeline_logs = db.execute(
        text("""
            SELECT log_id, pipeline_name, status, records_processed, records_failed, duration_seconds, started_at
            FROM pipeline_execution_logs
            ORDER BY log_id DESC LIMIT 10
        """)
    ).mappings().all()

    dedup_logs = db.execute(
        text("""
            SELECT log_id, master_transaction_id, applied_rule, similarity_score, reason, created_at
            FROM log_dedup
            ORDER BY log_id DESC LIMIT 10
        """)
    ).mappings().all()

    return {
        "counts": {
            "fact_transactions": int(fact_count),
            "stg_raw_emails": int(stg_email_cnt),
            "stg_raw_statements": int(stg_stmt_cnt),
            "stg_raw_receipts": int(stg_rcpt_cnt),
            "log_dedup": int(dedup_cnt),
        },
        "recent_pipelines": [dict(r) for r in pipeline_logs],
        "recent_dedup": [dict(r) for r in dedup_logs],
    }


@router.get("/data-quality")
def check_data_quality(db: Session = Depends(get_db)):
    """Chạy 5 luật kiểm thử chất lượng dữ liệu tự động theo tiêu chí Đề cương."""
    return DataQualityChecker.run_all_checks(db)
