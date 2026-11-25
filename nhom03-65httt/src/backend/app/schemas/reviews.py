"""Schemas cho tìm kiếm và phân trang đánh giá (EduVision BI, Nhóm 03).

Quy tắc:
- HA2.5: Kiểm tra kiểu dữ liệu chuẩn, ngày sai định dạng trả 422.
- HA2.6: Che thông tin cá nhân: tuyệt đối không chứa tên tác giả hay hồ sơ cá nhân.
"""

from __future__ import annotations

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class ReviewItemOut(BaseModel):
    review_key: int = Field(description="Khóa định danh đánh giá trong kho dữ liệu")
    review_id: str = Field(description="Mã đánh giá gốc từ nền tảng")
    platform: str = Field(description="Tên nền tảng E-learning")
    source: str = Field(description="Nguồn thu thập (Google Play, App Store, YouTube...)")
    rating: Optional[int] = Field(default=None, description="Số sao đánh giá (1-5)")
    created_at: Optional[str] = Field(default=None, description="Ngày đăng đánh giá (YYYY-MM-DD)")
    text: Optional[str] = Field(default=None, description="Nội dung đánh giá đã làm sạch")
    sentiment: Optional[str] = Field(default=None, description="Nhãn cảm xúc (Tích cực, Tiêu cực, Trung lập)")
    sentiment_score: Optional[float] = Field(default=None, description="Điểm cảm xúc (-1.0 đến 1.0)")
    aspect: Optional[str] = Field(default=None, description="Khía cạnh đánh giá chính")
    aspects: list[str] = Field(default_factory=list, description="Danh sách các khía cạnh liên quan")
    misaligned: bool = Field(default=False, description="Cờ lệch pha giữa số sao và cảm xúc")


class ReviewsListOut(BaseModel):
    total: int = Field(description="Tổng số đánh giá thỏa mãn điều kiện lọc")
    page: int = Field(description="Trang hiện tại (1-based)")
    page_size: int = Field(description="Số lượng đánh giá mỗi trang")
    total_pages: int = Field(description="Tổng số trang")
    items: list[ReviewItemOut] = Field(description="Danh sách đánh giá của trang hiện tại")
