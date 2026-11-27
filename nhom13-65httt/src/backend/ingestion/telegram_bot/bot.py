import asyncio
import logging
import os
import tempfile
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import pytesseract

from api.dependencies import get_db_session
from etl_pipeline.pipeline_runner import ETLPipelineRunner
from .ocr_engine import ReceiptOCREngine

logger = logging.getLogger(__name__)


class FinanceTelegramBot:
    """Telegram Bot tiếp nhận ảnh biên lai, chạy OCR, khử trùng và nạp vào PostgreSQL."""

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        try:
            self.allowed_chat_id = int(chat_id) if chat_id else None
        except ValueError as exc:
            raise ValueError("TELEGRAM_CHAT_ID phải là chat ID dạng số.") from exc
        self.user_id = int(os.getenv("TELEGRAM_USER_ID", "1"))
        if self.user_id < 1:
            raise ValueError("TELEGRAM_USER_ID phải là số nguyên dương.")
        self.ocr_engine = ReceiptOCREngine()
        self.etl_runner = ETLPipelineRunner()

    def is_configured(self) -> bool:
        token = self.token.lower()
        return bool(token and "placeholder" not in token and not token.startswith("your_"))

    def handle_receipt_image(self, file_id: str, chat_id: int, local_image_path: str) -> dict:
        """Lưu kết quả OCR vào staging và chỉ nạp giao dịch mới vào ETL."""
        ocr_text, dto = self.ocr_engine.process_image(local_image_path, chat_id=chat_id)
        if dto:
            dto.user_id = self.user_id

        with get_db_session() as db:
            inserted = db.execute(
                text("""
                    INSERT INTO stg_raw_receipts (
                        telegram_file_id, telegram_chat_id, image_url, ocr_raw_text,
                        extracted_amount, extracted_date, extracted_merchant, parsed_status
                    ) VALUES (
                        :file_id, :chat_id, :image_url, :ocr_text,
                        :amount, :tx_time, :merchant, :status
                    )
                    ON CONFLICT (telegram_file_id) DO NOTHING
                    RETURNING id
                """),
                {
                    "file_id": file_id,
                    "chat_id": chat_id,
                    "image_url": f"telegram://{file_id}",
                    "ocr_text": ocr_text,
                    "amount": abs(dto.amount) if dto else None,
                    "tx_time": dto.transaction_time if dto else None,
                    "merchant": dto.counterparty_name if dto else None,
                    "status": "PARSED" if dto else "FAILED",
                },
            ).first()

        if not inserted:
            return {
                "status": "duplicate",
                "message": "Ảnh này đã được tiếp nhận trước đó; không nạp lại giao dịch.",
            }

        if not dto:
            return {
                "status": "failed",
                "message": "Không nhận diện được số tiền hoặc ngày giao dịch hợp lệ từ ảnh biên lai.",
            }

        summary = self.etl_runner.run(
            [dto],
            pipeline_name=f"Ingestion_Telegram_U{self.user_id}",
            user_id=self.user_id,
        )
        if summary["failed"]:
            return {
                "status": "failed",
                "message": "Đã đọc ảnh nhưng không thể nạp giao dịch vào PostgreSQL.",
                "etl_summary": summary,
            }
        if summary["inserted"] == 0 and summary["deduplicated"] > 0:
            return {
                "status": "duplicate",
                "message": "Giao dịch đã tồn tại; hệ thống đã ghi nhận là trùng và không nạp lại.",
                "etl_summary": summary,
            }

        return {
            "status": "success",
            "extracted": {
                "amount": abs(dto.amount),
                "date": dto.transaction_time.isoformat(),
                "merchant": dto.counterparty_name,
                "description": dto.raw_description,
            },
            "etl_summary": summary,
        }

    def start_polling(self):
        """Khởi động bot; chỉ xử lý ảnh từ TELEGRAM_CHAT_ID đã cấu hình."""
        if not self.is_configured():
            raise RuntimeError("Cần cấu hình TELEGRAM_BOT_TOKEN trước khi chạy bot.")
        if self.allowed_chat_id is None:
            raise RuntimeError("Cần cấu hình TELEGRAM_CHAT_ID để giới hạn người gửi được phép.")

        from telegram import Update
        from telegram.error import TelegramError
        from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

        async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if update.effective_chat and update.effective_chat.id == self.allowed_chat_id:
                await update.message.reply_text(
                    "Xin chào! Hãy gửi ảnh biên lai, tôi sẽ trích xuất và ghi nhận giao dịch."
                )

        async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not update.effective_chat or update.effective_chat.id != self.allowed_chat_id:
                return

            message = update.effective_message
            if not message:
                return
            telegram_file = message.photo[-1] if message.photo else message.document
            if not telegram_file:
                return
            if telegram_file.file_size and telegram_file.file_size > 10 * 1024 * 1024:
                await message.reply_text("Ảnh quá lớn; vui lòng gửi ảnh nhỏ hơn 10 MB.")
                return

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                image_path = tmp.name
            try:
                downloaded_file = await telegram_file.get_file()
                await downloaded_file.download_to_drive(image_path)
                result = await asyncio.to_thread(
                    self.handle_receipt_image,
                    telegram_file.file_id,
                    update.effective_chat.id,
                    image_path,
                )
                if result["status"] == "success":
                    ext = result["extracted"]
                    await message.reply_text(
                        f"Đã ghi nhận giao dịch!\n"
                        f"- Số tiền: {ext['amount']:,.0f} VND\n"
                        f"- Ngày: {ext['date']}\n"
                        f"- Nội dung: {ext['description']}"
                    )
                else:
                    await message.reply_text(result["message"])
            except (
                OSError,
                RuntimeError,
                ValueError,
                SQLAlchemyError,
                pytesseract.TesseractError,
                TelegramError,
            ):
                logger.exception("Không thể xử lý ảnh biên lai Telegram.")
                await message.reply_text(
                    "Xử lý ảnh thất bại. Vui lòng kiểm tra log backend hoặc thử lại với ảnh rõ hơn."
                )
            finally:
                Path(image_path).unlink(missing_ok=True)

        app = (
            ApplicationBuilder()
            .token(self.token)
            .build()
        )
        app.add_handler(CommandHandler("start", start_cmd))
        app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, photo_handler))
        app.run_polling()


def main():
    logging.basicConfig(level=logging.INFO)
    FinanceTelegramBot().start_polling()


if __name__ == "__main__":
    main()
