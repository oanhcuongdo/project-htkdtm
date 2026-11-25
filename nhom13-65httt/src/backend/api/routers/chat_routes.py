from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from ai_service.chat_agent.gemini_agent import GeminiFinanceChatAgent
from api.dependencies import get_db
from api.security import get_current_user

router = APIRouter(prefix="/api/v1/chat", tags=["Gemini AI Cashflow Chat"])


class ChatAskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)
    session_id: str = "default"


@router.post("/ask")
def ask_cashflow_ai(
    payload: ChatAskRequest,
    current_user: dict = Depends(get_current_user),
):
    """Hỏi đáp dòng tiền cá nhân bằng tiếng Việt với Google Gemini (dữ liệu thật theo user_id)."""
    try:
        agent = GeminiFinanceChatAgent(user_id=int(current_user["user_id"]))
        return agent.ask(question=payload.question.strip(), session_id=payload.session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lỗi khi gọi Gemini AI Agent: {exc}")


@router.get("/history")
def get_chat_history(
    session_id: str = "default",
    limit: int = 30,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lấy lịch sử hội thoại Chat AI của người dùng hiện tại."""
    uid = int(current_user["user_id"])
    rows = db.execute(
        text("""
            SELECT message_id, role, content, structured_data, tools_used, created_at
            FROM chat_messages
            WHERE user_id = :uid AND session_id = :sid
            ORDER BY message_id ASC
            LIMIT :lim
        """),
        {"uid": uid, "sid": session_id, "lim": limit},
    ).mappings().all()

    return {"user_id": uid, "messages": [dict(r) for r in rows]}


@router.delete("/history")
def clear_chat_history(
    session_id: str = "default",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Xóa lịch sử hội thoại để bắt đầu phiên hỏi đáp mới."""
    uid = int(current_user["user_id"])
    db.execute(
        text("DELETE FROM chat_messages WHERE user_id = :uid AND session_id = :sid"),
        {"uid": uid, "sid": session_id},
    )
    db.commit()
    return {"status": "cleared"}
