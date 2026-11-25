from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class InteractionCreate(BaseModel):
    session_id: str = Field(min_length=3, max_length=100)
    fact_id: str
    action_type: Literal["view", "wishlist", "unwishlist", "compare", "contact_click"]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InteractionResponse(BaseModel):
    status: str = "ok"
    fact_id: str
    action_type: str


class SearchHistoryCreate(BaseModel):
    session_id: str = Field(min_length=3, max_length=100)
    raw_query: Optional[str] = None
    parsed_filters: Dict[str, Any] = Field(default_factory=dict)
    results_count: int = 0


class SearchHistoryDTO(BaseModel):
    search_id: int
    session_id: str
    raw_query: Optional[str] = None
    parsed_filters: Dict[str, Any] = Field(default_factory=dict)
    results_count: int = 0
    created_at: Optional[str] = None
