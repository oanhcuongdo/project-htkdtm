from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api", tags=["Integrations (Upcoming)"])


@router.post("/recommendations")
def recommendations_placeholder(payload: Dict[str, Any]):
    """Điểm chờ Giai đoạn 4: Hệ thống gợi ý AI (Vector Embedding + Matching Score)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Module Gợi ý AI sẽ được triển khai hoàn chỉnh ở Giai đoạn 4.",
    )


@router.post("/search/natural")
def natural_search_placeholder(payload: Dict[str, Any]):
    """Điểm chờ Gói Chức năng 1: Phân tích câu tìm kiếm tiếng Việt tự nhiên qua Gemini."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Module Tìm kiếm ngôn ngữ tự nhiên thuộc Gói Chức năng 1.",
    )
