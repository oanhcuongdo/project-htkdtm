import logging
import os
import tempfile
from sqlalchemy import text

from api.dependencies import get_db_session
from etl_pipeline.pipeline_runner import ETLPipelineRunner
from .ocr_engine import ReceiptOCREngine

logger = logging.getLogger(__name__)


class FinanceTelegramBot:
    """
    Telegram Bot tiếp nhận ảnh chụp hóa đơn/biên lai chuyển khoản và chạy OCR + ETL tự động.
    """

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.ocr_engine = ReceiptOCREngine()
        self.etl_runner = ETLPipelineRunner()

    def is_configured(self) -> bool:
        return bool(self.token and "placeholder" not in self.token)

    def handle_receipt_image(self, file_id: str, chat_id: int, local_image_path: str) -> dict:
        """Xử lý ảnh biên lai: chạy OCR, lưu staging stg_raw_receipts, đẩy qua ETL vào Data Warehouse."""
        ocr_text, dto = self.ocr_engine.process_image(local_image_path, chat_id=chat_id)

        with get_db_session() as db:
            db.execute(
                text("""
                    INSERT INTO stg_raw_receipts (
                        telegram_file_id, telegram_chat_id, image_url, ocr_raw_text,
                        extracted_amount, extracted_date, extracted_merchant, parsed_status
                    ) VALUES (
                        :file_id, :chat_id, :img_path, :ocr_text,
                        :amt, :dt, :merch, :status
                    )
                """),
                {
                    "file_id": file_id,
                    "chat_id": chat_id,
                    "img_path": local_image_path,
                    "ocr_text": ocr_text,
                    "amt": abs(dto.amount) if dto else None,
                    "dt": dto.transaction_time if dto else None,
                    "merch": dto.counterparty_name if dto else None,
                    "status": "PARSED" if dto else "FAILED",
                },
            )

        if not dto:
            return {"status": "failed", "message": "Không nhận diện được số tiền từ ảnh biên lai."}

        etl_summary = self.etl_runner.run([dto], pipeline_name="Ingestion_Telegram_OCR")
        return {
            "status": "success",
            "extracted": {
                "amount": abs(dto.amount),
                "date": dto.transaction_time.isoformat(),
                "merchant": dto.counterparty_name,
                "description": dto.raw_description,
            },
            "etl_summary": etl_summary,
        }

    def start_polling(self):
        """Khởi động bot lắng nghe tin nhắn Telegram (khi đã cấu hình token thật)."""
        if not self.is_configured():
            logger.info("TELEGRAM_BOT_TOKEN chưa được cấu hình thật; bỏ qua chế độ polling.")
            return

        from telegram import Update
        from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

        async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                "Xin chào! Hãy gửi ảnh chụp hóa đơn hoặc biên lai chuyển khoản, tôi sẽ tự động bóc tách và ghi nhận chi tiêu vào Kho dữ liệu cho bạn."
            )

        async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            photo = update.message.photo[-1]
            tg_file = await photo.get_file()
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                await tg_file.download_to_drive(tmp.name)
                result = self.handle_receipt_image(photo.file_id, update.effective_chat.id, tmp.name)
            if result["status"] == "success":
                ext = result["extracted"]
                await update.message.reply_text(
                    f"Đã ghi nhận giao dịch!\n- Số tiền: {ext['amount']:,.0f} VND\n- Ngày: {ext['date']}\n- Mô tả: {ext['description']}"
                )
            else:
                await update.message.reply_text(result["message"])

        app = ApplicationBuilder().token(self.token).build()
        app.add_handler(CommandHandler("start", start_cmd))
        app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
        app.run_polling()
