from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, status
from supabase import Client

from src.backend.api.dependencies import get_current_user_optional, get_db
from src.backend.api.schemas.chatbot import ChatbotQueryRequest, ChatbotQueryResponse
from src.backend.api.services.chatbot_service import chatbot_service

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot BI (Text-to-SQL)"])


@router.post("/query", response_model=ChatbotQueryResponse, status_code=status.HTTP_200_OK)
def handle_chatbot_query(
    payload: ChatbotQueryRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    db: Client = Depends(get_db),
):
    """
    Điểm cuối Chatbot BI Text-to-SQL:
    - Tiếp nhận câu hỏi tiếng Việt tự nhiên của người dùng.
    - Phân quyền RBAC (admin xem đầy đủ phân tích rủi ro/báo cáo; renter xem tin active an toàn).
    - Sinh câu SELECT và kiểm duyệt AST nghiêm ngặt qua sqlglot (chỉ 1 câu SELECT, ép LIMIT <= 100).
    - Thực thi qua RPC READ ONLY và trả về Insight kèm dữ liệu biểu đồ (bar, line, pie, table).
    """
    user_role = "admin" if (current_user and current_user.get("role") == "admin") else "renter"
    return chatbot_service.process_query(db=db, user_query=payload.query, role=user_role)
