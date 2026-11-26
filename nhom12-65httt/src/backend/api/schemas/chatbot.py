from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ChatbotQueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="Câu hỏi tự nhiên bằng tiếng Việt về thị trường phòng trọ Hà Nội."
    )
    session_id: Optional[str] = Field(
        default=None,
        description="ID phiên làm việc của người dùng."
    )


class ChatbotQueryResponse(BaseModel):
    query: str
    sql: str
    chart_type: Literal["bar", "line", "pie", "table"]
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int
    insight: str
    role: str
