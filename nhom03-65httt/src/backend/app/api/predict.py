"""Điểm cuối AI: hiện là KHUNG, trả 501 cho tới khi mô hình/LLM được tích hợp.

Hợp đồng (đường dẫn, dữ liệu vào) được chốt sớm để website và n8n có thể gọi thử.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.common import ChatIn, ErrorOut, TextIn

router = APIRouter(prefix="/api/v1", tags=["AI (khung, chưa tích hợp)"])

_NOT_READY = {501: {"model": ErrorOut, "description": "Chưa tích hợp"}}


def _not_implemented(what: str) -> HTTPException:
    return HTTPException(status_code=501, detail=f"{what} chưa được tích hợp")


@router.post("/predict/sentiment", responses=_NOT_READY, summary="Dự đoán cảm xúc 3 lớp (M1, PhoBERT)")
def predict_sentiment(payload: TextIn) -> None:
    raise _not_implemented("Mô hình cảm xúc M1")


@router.post("/predict/aspects", responses=_NOT_READY, summary="Dự đoán cảm xúc theo khía cạnh (M2, ABSA)")
def predict_aspects(payload: TextIn) -> None:
    raise _not_implemented("Mô hình khía cạnh M2")


@router.get("/forecast/{platform_id}", responses=_NOT_READY, summary="Dự báo tháng kế tiếp theo nền tảng (M3)")
def forecast(platform_id: str) -> None:
    raise _not_implemented("Mô hình dự báo M3")


@router.post("/chat", responses=_NOT_READY, summary="Chatbot LLM hỏi đáp trên số liệu")
def chat(payload: ChatIn) -> None:
    raise _not_implemented("Chatbot LLM")
