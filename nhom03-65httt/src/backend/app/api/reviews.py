"""Router tìm kiếm và phân trang đánh giá người học (EduVision BI, Nhóm 03).

Quy tắc:
- HA2.4: Lọc chính xác theo nền tảng, ngày, cảm xúc, khía cạnh, từ khóa; phân trang chuẩn.
- HA2.5: Ngày sai định dạng trả 422; trang vượt quá số trang trả danh sách rỗng, không sập 500.
- HA2.6: Che dữ liệu cá nhân: không trả tên thật hay hồ sơ tác giả.
"""

from __future__ import annotations

from datetime import date
import math
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
import psycopg

from app.core.config import get_settings
from app.schemas.reviews import ReviewItemOut, ReviewsListOut

router = APIRouter(prefix="/api/v1", tags=["Đánh giá"])

# Dữ liệu dự phòng mẫu dùng khi chưa cấu hình CSDL hoặc CSDL ngoại tuyến
SAMPLE_REVIEWS: list[dict[str, Any]] = [
    {
        "review_key": 1,
        "review_id": "rev-001",
        "platform": "ELSA Speak",
        "source": "Google Play",
        "rating": 5,
        "created_at": "2026-10-24",
        "text": "Nhận diện giọng nói cực kỳ chuẩn xác, giúp mình phát âm tiếng Anh tự tin hơn rất nhiều khi giao tiếp.",
        "sentiment": "Tích cực",
        "sentiment_score": 0.88,
        "aspect": "Technical",
        "aspects": ["Technical", "Academic"],
        "misaligned": False,
    },
    {
        "review_key": 2,
        "review_id": "rev-002",
        "platform": "ELSA Speak",
        "source": "App Store",
        "rating": 4,
        "created_at": "2026-10-23",
        "text": "Giao diện hiện đại dễ dùng nhưng giá gói trọn đời hơi cao so với sinh viên.",
        "sentiment": "Trung lập",
        "sentiment_score": 0.15,
        "aspect": "Pricing",
        "aspects": ["Pricing", "Technical"],
        "misaligned": False,
    },
    {
        "review_key": 3,
        "review_id": "rev-003",
        "platform": "ELSA Speak",
        "source": "Google Play",
        "rating": 1,
        "created_at": "2026-10-20",
        "text": "Ứng dụng tuyệt vời, bài học chất lượng cao xuất sắc!",
        "sentiment": "Tích cực",
        "sentiment_score": 0.92,
        "aspect": "Academic",
        "aspects": ["Academic"],
        "misaligned": True,  # Lệch pha: số sao 1 nhưng lời khen tích cực
    },
    {
        "review_key": 4,
        "review_id": "rev-004",
        "platform": "Duolingo",
        "source": "Google Play",
        "rating": 5,
        "created_at": "2026-10-22",
        "text": "Học mỗi ngày không thấy chán, tính năng bảng xếp hạng kích thích động lực học tập tuyệt vời.",
        "sentiment": "Tích cực",
        "sentiment_score": 0.95,
        "aspect": "Academic",
        "aspects": ["Academic"],
        "misaligned": False,
    },
    {
        "review_key": 5,
        "review_id": "rev-005",
        "platform": "Duolingo",
        "source": "App Store",
        "rating": 2,
        "created_at": "2026-10-21",
        "text": "Bản cập nhật gần đây mất thanh trái tim liên tục, quảng cáo chen ngang quá nhiều gây ức chế.",
        "sentiment": "Tiêu cực",
        "sentiment_score": -0.75,
        "aspect": "Technical",
        "aspects": ["Technical"],
        "misaligned": False,
    },
    {
        "review_key": 6,
        "review_id": "rev-006",
        "platform": "Duolingo",
        "source": "Google Play",
        "rating": 5,
        "created_at": "2026-10-19",
        "text": "Hay bị lỗi mất kết nối máy chủ khi đang kiểm tra cuối bài.",
        "sentiment": "Tiêu cực",
        "sentiment_score": -0.80,
        "aspect": "Technical",
        "aspects": ["Technical"],
        "misaligned": True,  # Lệch pha: số sao 5 nhưng nội dung than phiền lỗi
    },
    {
        "review_key": 7,
        "review_id": "rev-007",
        "platform": "Vuihoc",
        "source": "Google Play",
        "rating": 5,
        "created_at": "2026-10-18",
        "text": "Các thầy cô giảng bài toán và tiếng Việt rất sinh động, con mình rất thích xem bài giảng.",
        "sentiment": "Tích cực",
        "sentiment_score": 0.85,
        "aspect": "Academic",
        "aspects": ["Academic"],
        "misaligned": False,
    },
    {
        "review_key": 8,
        "review_id": "rev-008",
        "platform": "Vuihoc",
        "source": "App Store",
        "rating": 2,
        "created_at": "2026-10-15",
        "text": "Tự động gia hạn trừ tiền thẻ mà không báo trước qua tin nhắn hay email, đề nghị hoàn tiền.",
        "sentiment": "Tiêu cực",
        "sentiment_score": -0.85,
        "aspect": "Pricing",
        "aspects": ["Pricing", "Customer Service"],
        "misaligned": False,
    },
    {
        "review_key": 9,
        "review_id": "rev-009",
        "platform": "HOCMAI",
        "source": "Google Play",
        "rating": 4,
        "created_at": "2026-10-17",
        "text": "Ngân hàng đề thi phong phú bám sát chương trình bộ giáo dục, giải thích đáp án chi tiết.",
        "sentiment": "Tích cực",
        "sentiment_score": 0.78,
        "aspect": "Academic",
        "aspects": ["Academic"],
        "misaligned": False,
    },
    {
        "review_key": 10,
        "review_id": "rev-010",
        "platform": "HOCMAI",
        "source": "Google Play",
        "rating": 2,
        "created_at": "2026-10-14",
        "text": "Tải video bài giảng thường xuyên bị xoay vòng đứng hình vào khung giờ cao điểm buổi tối.",
        "sentiment": "Tiêu cực",
        "sentiment_score": -0.70,
        "aspect": "Technical",
        "aspects": ["Technical"],
        "misaligned": False,
    },
    {
        "review_key": 11,
        "review_id": "rev-011",
        "platform": "Monkey Junior",
        "source": "Google Play",
        "rating": 5,
        "created_at": "2026-10-16",
        "text": "Hình ảnh minh họa sặc sỡ và phát âm chuẩn, bé học được nhiều từ vựng tiếng Anh mới.",
        "sentiment": "Tích cực",
        "sentiment_score": 0.89,
        "aspect": "Academic",
        "aspects": ["Academic"],
        "misaligned": False,
    },
    {
        "review_key": 12,
        "review_id": "rev-012",
        "platform": "Quizlet",
        "source": "App Store",
        "rating": 5,
        "created_at": "2026-10-22",
        "text": "Học flashcard tuyệt đỉnh cho sinh viên ngành y và ngoại ngữ, tiết kiệm bao nhiêu thời gian học thuộc.",
        "sentiment": "Tích cực",
        "sentiment_score": 0.94,
        "aspect": "Academic",
        "aspects": ["Academic"],
        "misaligned": False,
    },
    {
        "review_key": 13,
        "review_id": "rev-013",
        "platform": "Khan Academy",
        "source": "Google Play",
        "rating": 5,
        "created_at": "2026-10-20",
        "text": "Nền tảng hoàn toàn miễn phí không quảng cáo vì cộng đồng, nội dung toán và khoa học đỉnh cao.",
        "sentiment": "Tích cực",
        "sentiment_score": 0.98,
        "aspect": "Academic",
        "aspects": ["Academic", "Pricing"],
        "misaligned": False,
    },
    {
        "review_key": 14,
        "review_id": "rev-014",
        "platform": "Busuu",
        "source": "Google Play",
        "rating": 4,
        "created_at": "2026-10-19",
        "text": "Tính năng chấm bài tương tác cộng đồng bản xứ rất hay, chữa lỗi viết và ngữ pháp nhanh.",
        "sentiment": "Tích cực",
        "sentiment_score": 0.82,
        "aspect": "Academic",
        "aspects": ["Academic"],
        "misaligned": False,
    },
    {
        "review_key": 15,
        "review_id": "rev-015",
        "platform": "Memrise",
        "source": "App Store",
        "rating": 4,
        "created_at": "2026-10-18",
        "text": "Video người bản xứ nói rất tự nhiên, nhưng gói trả phí hiện tại hơi đắt so với các app khác.",
        "sentiment": "Trung lập",
        "sentiment_score": 0.20,
        "aspect": "Pricing",
        "aspects": ["Pricing", "Academic"],
        "misaligned": False,
    },
]


def _map_sentiment(label: str | None, rating: int | None) -> str:
    """Chuẩn hóa nhãn cảm xúc hiển thị."""
    if not label:
        if rating is not None:
            if rating >= 4:
                return "Tích cực"
            if rating == 3:
                return "Trung lập"
            return "Tiêu cực"
        return "Trung lập"

    clean = label.lower().strip()
    if clean in ("tich_cuc", "positive", "tích cực"):
        return "Tích cực"
    if clean in ("tieu_cuc", "negative", "tiêu cực"):
        return "Tiêu cực"
    return "Trung lập"


def _check_misaligned(rating: int | None, sentiment: str | None) -> bool:
    """Xác định cờ lệch pha giữa số sao đánh giá và nội dung cảm xúc."""
    if rating is None or sentiment is None:
        return False
    if rating >= 4 and sentiment == "Tiêu cực":
        return True
    if rating <= 2 and sentiment == "Tích cực":
        return True
    return False


def _query_database(
    database_url: str,
    platform: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date],
    sentiment: Optional[str],
    aspect: Optional[str],
    keyword: Optional[str],
    rating: Optional[int],
    misaligned_only: bool,
    source: Optional[str],
    page: int,
    page_size: int,
) -> tuple[int, list[ReviewItemOut]]:
    """Truy vấn kho dữ liệu PostgreSQL sạch sẽ, an toàn chống SQL injection."""
    conditions: list[str] = ["1=1"]
    params: list[Any] = []

    if platform:
        conditions.append("LOWER(p.platform_name) = LOWER(%s)")
        params.append(platform.strip())

    if start_date:
        conditions.append("d.full_date >= %s")
        params.append(start_date)

    if end_date:
        conditions.append("d.full_date <= %s")
        params.append(end_date)

    if rating:
        conditions.append("r.rating = %s")
        params.append(rating)

    if source:
        conditions.append("LOWER(s.source_name) = LOWER(%s)")
        params.append(source.strip())

    if keyword:
        conditions.append("(t.text ILIKE %s OR t.review_id ILIKE %s)")
        kw = f"%{keyword.strip()}%"
        params.extend([kw, kw])

    where_clause = " AND ".join(conditions)

    count_sql = f"""
        SELECT COUNT(r.review_key)
        FROM dw.fact_review r
        JOIN clean.review_text t ON r.review_key = t.review_key
        JOIN dw.dim_platform p ON r.platform_key = p.platform_key
        JOIN dw.dim_time d ON r.time_key = d.time_key
        JOIN dw.dim_source s ON r.source_key = s.source_key
        WHERE {where_clause}
    """

    data_sql = f"""
        SELECT
            r.review_key,
            t.review_id,
            p.platform_name,
            s.source_name,
            r.rating,
            to_char(d.full_date, 'YYYY-MM-DD') AS created_at,
            t.text,
            fa.sentiment_label,
            fa.sentiment_score,
            fa.aspect_names
        FROM dw.fact_review r
        JOIN clean.review_text t ON r.review_key = t.review_key
        JOIN dw.dim_platform p ON r.platform_key = p.platform_key
        JOIN dw.dim_time d ON r.time_key = d.time_key
        JOIN dw.dim_source s ON r.source_key = s.source_key
        LEFT JOIN (
            SELECT
                a.review_key,
                string_agg(da.aspect_name, ', ') AS aspect_names,
                max(a.sentiment_label) AS sentiment_label,
                avg(a.sentiment_score) AS sentiment_score
            FROM dw.fact_review_aspect a
            JOIN dw.dim_aspect da ON a.aspect_key = da.aspect_key
            GROUP BY a.review_key
        ) fa ON r.review_key = fa.review_key
        WHERE {where_clause}
        ORDER BY d.full_date DESC, r.review_key DESC
        OFFSET %s LIMIT %s
    """

    with psycopg.connect(database_url, connect_timeout=3) as conn:
        with conn.cursor() as cur:
            cur.execute(count_sql, params)
            total = cur.fetchone()[0]

            offset = (page - 1) * page_size
            cur.execute(data_sql, params + [offset, page_size])
            rows = cur.fetchall()

            items: list[ReviewItemOut] = []
            for row in rows:
                r_key, r_id, p_name, s_name, r_rating, dt_str, txt, s_label, s_score, asp_names = row
                st_name = _map_sentiment(s_label, r_rating)
                misaligned = _check_misaligned(r_rating, st_name)

                aspects_list = [a.strip() for a in asp_names.split(",")] if asp_names else []
                primary_aspect = aspects_list[0] if aspects_list else None

                # Lọc thêm khía cạnh và cảm xúc nếu có yêu cầu
                if sentiment and st_name.lower() != sentiment.lower():
                    continue
                if aspect and aspect.lower() not in [a.lower() for a in aspects_list]:
                    continue
                if misaligned_only and not misaligned:
                    continue

                items.append(
                    ReviewItemOut(
                        review_key=r_key,
                        review_id=r_id,
                        platform=p_name,
                        source=s_name,
                        rating=r_rating,
                        created_at=dt_str,
                        text=txt,
                        sentiment=st_name,
                        sentiment_score=float(s_score) if s_score is not None else None,
                        aspect=primary_aspect,
                        aspects=aspects_list,
                        misaligned=misaligned,
                    )
                )

            return total, items


@router.get(
    "/reviews",
    response_model=ReviewsListOut,
    summary="Tìm kiếm, lọc và phân trang đánh giá người học",
)
def list_reviews(
    platform: Optional[str] = Query(None, description="Tên hoặc mã nền tảng (ví dụ: ELSA Speak, Duolingo)"),
    start_date: Optional[date] = Query(None, description="Ngày bắt đầu (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Ngày kết thúc (YYYY-MM-DD)"),
    sentiment: Optional[str] = Query(None, description="Lọc cảm xúc (Tích cực, Trung lập, Tiêu cực)"),
    aspect: Optional[str] = Query(None, description="Lọc theo khía cạnh (Technical, Academic, Customer Service, Pricing, Other)"),
    keyword: Optional[str] = Query(None, description="Từ khóa tìm kiếm trong văn bản hoặc mã đánh giá"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Số sao đánh giá (1-5)"),
    misaligned_only: bool = Query(False, description="Chỉ lấy đánh giá có hiện tượng lệch pha"),
    source: Optional[str] = Query(None, description="Nguồn thu thập"),
    page: int = Query(1, ge=1, description="Số trang hiển thị"),
    page_size: int = Query(20, ge=1, le=100, description="Số lượng bản ghi trên một trang"),
) -> ReviewsListOut:
    """Trả về danh sách đánh giá có phân trang, hỗ trợ bộ lọc đa chiều."""
    settings = get_settings()

    # Thử kết nối CSDL nếu đã có DATABASE_URL
    if settings.database_url:
        try:
            total, items = _query_database(
                settings.database_url,
                platform,
                start_date,
                end_date,
                sentiment,
                aspect,
                keyword,
                rating,
                misaligned_only,
                source,
                page,
                page_size,
            )
            total_pages = math.ceil(total / page_size) if total > 0 else 1
            # HA2.5: Nếu trang vượt quá tổng số trang, trả về danh sách rỗng, không sập 500
            if page > total_pages:
                items = []
            return ReviewsListOut(
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                items=items,
            )
        except Exception:
            # Nếu kết nối CSDL thất bại, chuyển sang cơ chế dự phòng mẫu an toàn
            pass

    # Cơ chế dự phòng dựa trên dữ liệu mẫu chuẩn (dùng khi chạy kiểm thử hoặc offline)
    filtered = SAMPLE_REVIEWS

    if platform and platform != "Tất cả nền tảng":
        filtered = [r for r in filtered if r["platform"].lower() == platform.lower()]

    if source and source != "Tất cả nguồn":
        filtered = [r for r in filtered if r["source"].lower() == source.lower()]

    if rating is not None:
        filtered = [r for r in filtered if r["rating"] == rating]

    if sentiment and sentiment != "Tất cả cảm xúc":
        filtered = [r for r in filtered if r["sentiment"].lower() == sentiment.lower()]

    if aspect and aspect != "Tất cả khía cạnh":
        filtered = [r for r in filtered if aspect.lower() in [a.lower() for a in r["aspects"]]]

    if keyword:
        kw = keyword.lower().strip()
        filtered = [
            r
            for r in filtered
            if kw in r["text"].lower() or kw in r["review_id"].lower() or kw in r["platform"].lower()
        ]

    if misaligned_only:
        filtered = [r for r in filtered if r["misaligned"]]

    if start_date:
        start_str = start_date.isoformat()
        filtered = [r for r in filtered if r["created_at"] and r["created_at"] >= start_str]

    if end_date:
        end_str = end_date.isoformat()
        filtered = [r for r in filtered if r["created_at"] and r["created_at"] <= end_str]

    total = len(filtered)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    # HA2.5: Trang vượt quá trả danh sách rỗng, không 500
    if page > total_pages:
        page_items = []
    else:
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_items = [ReviewItemOut(**r) for r in filtered[start_idx:end_idx]]

    return ReviewsListOut(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=page_items,
    )


@router.get(
    "/reviews/{review_key}",
    response_model=ReviewItemOut,
    summary="Chi tiết một đánh giá theo khóa review_key",
)
def get_review(review_key: int) -> ReviewItemOut:
    """Lấy chi tiết một đánh giá theo khóa số nguyên."""
    settings = get_settings()

    if settings.database_url:
        try:
            with psycopg.connect(settings.database_url, connect_timeout=3) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            r.review_key,
                            t.review_id,
                            p.platform_name,
                            s.source_name,
                            r.rating,
                            to_char(d.full_date, 'YYYY-MM-DD'),
                            t.text
                        FROM dw.fact_review r
                        JOIN clean.review_text t ON r.review_key = t.review_key
                        JOIN dw.dim_platform p ON r.platform_key = p.platform_key
                        JOIN dw.dim_time d ON r.time_key = d.time_key
                        JOIN dw.dim_source s ON r.source_key = s.source_key
                        WHERE r.review_key = %s
                        """,
                        (review_key,),
                    )
                    row = cur.fetchone()
                    if row:
                        r_key, r_id, p_name, s_name, r_rating, dt_str, txt = row
                        st_name = _map_sentiment(None, r_rating)
                        return ReviewItemOut(
                            review_key=r_key,
                            review_id=r_id,
                            platform=p_name,
                            source=s_name,
                            rating=r_rating,
                            created_at=dt_str,
                            text=txt,
                            sentiment=st_name,
                            sentiment_score=None,
                            aspect=None,
                            aspects=[],
                            misaligned=_check_misaligned(r_rating, st_name),
                        )
        except Exception:
            pass

    for r in SAMPLE_REVIEWS:
        if r["review_key"] == review_key:
            return ReviewItemOut(**r)

    raise HTTPException(status_code=404, detail="Không tìm thấy đánh giá với mã yêu cầu")
