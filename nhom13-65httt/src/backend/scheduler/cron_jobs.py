import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text

from api.dependencies import get_db_session
from etl_pipeline.pipeline_runner import ETLPipelineRunner
from ingestion.email_collector.imap_client import IMAPEmailCollector
from ingestion.statement_parser import StatementTabularParser, StatementPDFParser

logger = logging.getLogger(__name__)

WATCH_FOLDER = "/app/watch_statements"
scheduler = BackgroundScheduler()


def job_poll_emails():
    """Tác vụ định kỳ mỗi 15 phút: quét email biến động số dư và đẩy vào Kho dữ liệu."""
    collector = IMAPEmailCollector()
    if not collector.is_configured():
        return
    dtos = collector.collect_and_stage()
    if dtos:
        runner = ETLPipelineRunner()
        summary = runner.run(dtos, pipeline_name="Scheduled_Email_Collector")
        logger.info(f"Email job hoàn thành: {summary}")


def scan_watch_folder(force_rescan: bool = False) -> dict:
    """Quét thư mục watch_statements tìm các file sao kê mới chưa được nạp."""
    if not os.path.isdir(WATCH_FOLDER):
        return {"scanned_files": 0, "details": []}

    with get_db_session() as db:
        rows = db.execute(text("SELECT DISTINCT file_name FROM stg_raw_statements")).fetchall()
        already_processed = {r[0] for r in rows}

    tabular_parser = StatementTabularParser()
    pdf_parser = StatementPDFParser()
    runner = ETLPipelineRunner()
    details = []

    for fname in sorted(os.listdir(WATCH_FOLDER)):
        ext = os.path.splitext(fname)[1].lower()
        if ext not in (".xlsx", ".xls", ".csv", ".pdf"):
            continue
        if not force_rescan and fname in already_processed:
            continue

        fpath = os.path.join(WATCH_FOLDER, fname)
        if ext == ".pdf":
            dtos = pdf_parser.parse_file(fpath)
        else:
            dtos = tabular_parser.parse_file(fpath)

        summary = runner.run(dtos, pipeline_name=f"WatchFolder_{fname}")
        details.append({"file_name": fname, "summary": summary})

    return {"scanned_files": len(details), "details": details}


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(job_poll_emails, "interval", minutes=15, id="email_poll_job", replace_existing=True)
        scheduler.add_job(scan_watch_folder, "interval", minutes=5, id="watch_folder_job", replace_existing=True)
        scheduler.start()
        logger.info("APScheduler đã khởi động: Email (15 phút/lần), Watch Folder (5 phút/lần).")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
