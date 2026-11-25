from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from supabase import Client

from src.backend.api.dependencies import validate_uuid
from src.backend.api.schemas.interaction import (
    InteractionCreate,
    InteractionResponse,
    SearchHistoryCreate,
    SearchHistoryDTO,
)
from src.backend.api.schemas.listing import ListingCardDTO
from src.backend.api.services.listing_service import FACT_EMBEDDED_SELECT, flatten_fact_row


def record_interaction(
    db: Client,
    payload: InteractionCreate,
    user_id: Optional[str] = None,
) -> InteractionResponse:
    """Ghi nhận hành vi người dùng thật vào fact_user_interactions và cập nhật bộ đếm."""
    clean_fact_id = validate_uuid(payload.fact_id, "fact_id")
    fact_res = (
        db.table("fact_rental_listings")
        .select("view_count, wishlist_count")
        .eq("fact_id", clean_fact_id)
        .limit(1)
        .execute()
    )
    if not fact_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phòng trọ.")

    row: Dict[str, Any] = {
        "session_id": payload.session_id,
        "fact_id": clean_fact_id,
        "action_type": payload.action_type,
        "metadata": payload.metadata,
    }
    if user_id:
        row["user_id"] = user_id

    db.table("fact_user_interactions").insert(row).execute()

    if payload.action_type in ("view", "wishlist", "unwishlist"):
        cur = fact_res.data[0]
        updates: Dict[str, int] = {}
        if payload.action_type == "view":
            updates["view_count"] = int(cur.get("view_count") or 0) + 1
        elif payload.action_type == "wishlist":
            updates["wishlist_count"] = int(cur.get("wishlist_count") or 0) + 1
        elif payload.action_type == "unwishlist":
            updates["wishlist_count"] = max(0, int(cur.get("wishlist_count") or 0) - 1)
        db.table("fact_rental_listings").update(updates).eq("fact_id", clean_fact_id).execute()

    return InteractionResponse(fact_id=clean_fact_id, action_type=payload.action_type)


def get_wishlist(db: Client, session_id: str) -> List[ListingCardDTO]:
    """Lấy danh sách phòng đang nằm trong Wishlist của session_id."""
    logs = (
        db.table("fact_user_interactions")
        .select("fact_id, action_type, created_at")
        .eq("session_id", session_id)
        .in_("action_type", ["wishlist", "unwishlist"])
        .order("created_at", desc=False)
        .execute()
        .data
        or []
    )

    state: Dict[str, bool] = {}
    for entry in logs:
        state[str(entry["fact_id"])] = entry["action_type"] == "wishlist"

    active_ids = [fid for fid, kept in state.items() if kept]
    if not active_ids:
        return []

    facts = (
        db.table("fact_rental_listings")
        .select(FACT_EMBEDDED_SELECT)
        .in_("fact_id", active_ids)
        .execute()
        .data
        or []
    )
    return [ListingCardDTO(**flatten_fact_row(r)) for r in facts]


def save_search_history(
    db: Client,
    payload: SearchHistoryCreate,
    user_id: Optional[str] = None,
) -> SearchHistoryDTO:
    """Lưu lịch sử tìm kiếm của người dùng."""
    row: Dict[str, Any] = {
        "session_id": payload.session_id,
        "raw_query": payload.raw_query,
        "parsed_filters": payload.parsed_filters,
        "results_count": payload.results_count,
    }
    if user_id:
        row["user_id"] = user_id

    res = db.table("search_history").insert(row).execute()
    created = res.data[0]
    return SearchHistoryDTO(
        search_id=created["search_id"],
        session_id=created["session_id"],
        raw_query=created.get("raw_query"),
        parsed_filters=created.get("parsed_filters") or {},
        results_count=int(created.get("results_count") or 0),
        created_at=str(created.get("created_at")) if created.get("created_at") else None,
    )


def get_search_history(db: Client, session_id: str, limit: int = 15) -> List[SearchHistoryDTO]:
    """Lấy lịch sử tìm kiếm gần nhất theo session_id."""
    rows = (
        db.table("search_history")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )
    return [
        SearchHistoryDTO(
            search_id=r["search_id"],
            session_id=r["session_id"],
            raw_query=r.get("raw_query"),
            parsed_filters=r.get("parsed_filters") or {},
            results_count=int(r.get("results_count") or 0),
            created_at=str(r.get("created_at")) if r.get("created_at") else None,
        )
        for r in rows
    ]
