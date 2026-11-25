import logging
import os
import requests

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Kênh gửi cảnh báo tức thời (Anomaly Alert / Over-budget Alert) và bản tin tài chính tuần qua Telegram Bot.
    Hỗ trợ chế độ dry-run khi chưa cấu hình TELEGRAM_BOT_TOKEN thật.
    """

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    def is_configured(self) -> bool:
        return bool(
            self.token
            and self.chat_id
            and "placeholder" not in self.token
            and "demo" not in self.chat_id
        )

    def send_message(self, message_text: str, parse_mode: str = "Markdown") -> dict:
        if not self.is_configured():
            logger.info("Telegram chưa cấu hình token/chat_id thật -> chạy chế độ dry-run preview.")
            return {
                "sent": False,
                "mode": "dry_run_preview",
                "reason": "Chưa cấu hình TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID thật trong file .env",
                "preview_message": message_text,
            }

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            resp = requests.post(
                url,
                json={"chat_id": self.chat_id, "text": message_text, "parse_mode": parse_mode},
                timeout=10,
            )
            ok = resp.status_code == 200
            return {
                "sent": ok,
                "mode": "telegram_live",
                "http_status": resp.status_code,
                "preview_message": message_text,
            }
        except Exception as exc:
            logger.error(f"Lỗi gửi tin nhắn Telegram: {exc}")
            return {"sent": False, "mode": "error", "error": str(exc), "preview_message": message_text}
