from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from supabase import Client

from src.backend.api.dependencies import get_current_user_optional, get_db
from src.backend.api.schemas.interaction import (
    InteractionCreate,
    InteractionResponse,
    SearchHistoryCreate,
    SearchHistoryDTO,
)
from src.backend.api.schemas.listing import ListingCardDTO
from src.backend.api.services import interaction_service

router = APIRouter(prefix="/api", tags=["Interactions"])


@router.post("/interactions", response_model=InteractionResponse)
def record_interaction(
    payload: InteractionCreate,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    db: Client = Depends(get_db),
):
    """Ghi nhận hành vi người dùng thật (view, wishlist, unwishlist, compare, contact_click)."""
    user_id = user.get("sub") if user else None
    return interaction_service.record_interaction(db=db, payload=payload, user_id=user_id)


@router.get("/wishlist", response_model=List[ListingCardDTO])
def get_wishlist(
    session_id: str = Query(..., min_length=3, max_length=100),
    db: Client = Depends(get_db),
):
    """Lấy danh sách phòng đã lưu yêu thích theo session_id."""
    return interaction_service.get_wishlist(db=db, session_id=session_id)


@router.post("/search-history", response_model=SearchHistoryDTO)
def save_search_history(
    payload: SearchHistoryCreate,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    db: Client = Depends(get_db),
):
    """Lưu lịch sử tìm kiếm vào Supabase."""
    user_id = user.get("sub") if user else None
    return interaction_service.save_search_history(db=db, payload=payload, user_id=user_id)


@router.get("/search-history", response_model=List[SearchHistoryDTO])
def get_search_history(
    session_id: str = Query(..., min_length=3, max_length=100),
    limit: int = Query(15, ge=1, le=50),
    db: Client = Depends(get_db),
):
    """Lấy lịch sử tìm kiếm gần đây của người dùng."""
    return interaction_service.get_search_history(db=db, session_id=session_id, limit=limit)
