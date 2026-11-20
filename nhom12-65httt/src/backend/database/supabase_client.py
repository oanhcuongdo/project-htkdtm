import logging
from typing import Optional
from supabase import create_client, Client
from src.backend.config.settings import settings

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """Khởi tạo và trả về singleton instance của Supabase Client."""
    global _supabase_client
    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("SUPABASE_URL và SUPABASE_KEY phải được thiết lập trong .env")
        try:
            _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            logger.info("Đã kết nối thành công tới Supabase: %s", settings.SUPABASE_URL)
        except Exception as e:
            logger.error("Lỗi khởi tạo Supabase client: %s", e)
            raise e
    return _supabase_client

def test_connection() -> bool:
    """Kiểm tra kết nối và tính sẵn sàng của database Supabase."""
    try:
        client = get_supabase_client()
        res = client.table("dim_property_type").select("count", count="exact").execute()
        logger.info("Kết nối Supabase OK! Số loại phòng trọ: %s", res.count)
        return True
    except Exception as e:
        logger.error("Kiểm tra kết nối Supabase thất bại: %s", e)
        return False
