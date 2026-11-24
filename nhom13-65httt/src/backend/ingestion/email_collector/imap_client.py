import email
import imaplib
import logging
import os
from datetime import datetime
from email.header import decode_header
from typing import List, Tuple
from sqlalchemy import text

from api.dependencies import get_db_session
from ingestion.models import RawTransactionDTO
from .parsers import parse_bank_email

logger = logging.getLogger(__name__)


def _decode_mime_header(header_val: str) -> str:
    if not header_val:
        return ""
    decoded_parts = decode_header(header_val)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


class IMAPEmailCollector:
    """Thu thập email biến động số dư một chiều qua giao thức IMAP (Read-only)."""

    def __init__(self):
        self.imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
        self.email_address = os.getenv("IMAP_EMAIL", "")
        self.app_password = os.getenv("IMAP_APP_PASSWORD", "")

    def is_configured(self) -> bool:
        return bool(
            self.email_address
            and self.app_password
            and "placeholder" not in self.app_password
        )

    def fetch_recent_emails(self, limit: int = 50) -> List[Tuple[str, str, str, str, str, datetime]]:
        """Kết nối hộp thư và lấy danh sách email gần nhất."""
        if not self.is_configured():
            logger.info("IMAP chưa được cấu hình thông tin thật; bỏ qua bước poll hộp thư trực tiếp.")
            return []

        emails_data = []
        mail = imaplib.IMAP4_SSL(self.imap_server)
        try:
            mail.login(self.email_address, self.app_password)
            mail.select("INBOX", readonly=True)

            status, messages = mail.search(None, "UNSEEN")
            if status != "OK":
                return []

            msg_ids = messages[0].split()[-limit:]
            for msg_id in msg_ids:
                res, msg_data = mail.fetch(msg_id, "(RFC822)")
                if res != "OK":
                    continue
                msg = email.message_from_bytes(msg_data[0][1])

                message_id = msg.get("Message-ID", f"imap-{msg_id.decode()}")
                sender = _decode_mime_header(msg.get("From", ""))
                subject = _decode_mime_header(msg.get("Subject", ""))
                date_str = msg.get("Date", "")
                try:
                    received_at = email.utils.parsedate_to_datetime(date_str)
                except Exception:
                    received_at = datetime.now()

                body_html = ""
                body_text = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        ctype = part.get_content_type()
                        payload = part.get_payload(decode=True)
                        if not payload:
                            continue
                        decoded = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                        if ctype == "text/plain":
                            body_text += decoded
                        elif ctype == "text/html":
                            body_html += decoded
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body_text = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")

                emails_data.append((message_id, sender, subject, body_html, body_text, received_at))
        finally:
            try:
                mail.logout()
            except Exception:
                pass

        return emails_data

    def collect_and_stage(self) -> List[RawTransactionDTO]:
        """Thu thập email, lưu vào bảng staging stg_raw_emails và bóc tách giao dịch."""
        raw_emails = self.fetch_recent_emails()
        return self.process_raw_emails(raw_emails)

    def process_raw_emails(
        self, raw_emails: List[Tuple[str, str, str, str, str, datetime]]
    ) -> List[RawTransactionDTO]:
        """Lưu vết email thô vào Staging và gọi bộ parser theo từng ngân hàng."""
        parsed_transactions: List[RawTransactionDTO] = []

        with get_db_session() as db:
            for message_id, sender, subject, body_html, body_text, received_at in raw_emails:
                content_to_parse = body_text or body_html
                dto = parse_bank_email(sender, subject, content_to_parse)
                status = "PARSED" if dto else "FAILED"
                err = None if dto else "Không khớp định dạng mẫu ngân hàng được hỗ trợ"

                db.execute(
                    text("""
                        INSERT INTO stg_raw_emails (message_id, sender, subject, body_html, body_text, received_at, parsed_status, error_message)
                        VALUES (:msg_id, :sender, :subj, :html, :txt, :recv, :status, :err)
                        ON CONFLICT (message_id) DO NOTHING
                    """),
                    {
                        "msg_id": message_id,
                        "sender": sender,
                        "subj": subject,
                        "html": body_html,
                        "txt": body_text,
                        "recv": received_at,
                        "status": status,
                        "err": err,
                    },
                )
                if dto:
                    parsed_transactions.append(dto)

        return parsed_transactions
