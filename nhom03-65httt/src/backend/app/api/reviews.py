"""Router tìm kiếm và phân trang đánh giá người học (EduVision BI, Nhóm 03).

Quy tắc:
- HA2.4: Lọc chính xác ở mức SQL theo nền tảng, ngày, cảm xúc, khía cạnh, từ khóa; phân trang chuẩn.
- HA2.5: Ngày sai định dạng trả 422; trang vượt quá số trang trả danh sách rỗng, không sập 500.
- HA2.6: Che dữ liệu cá nhân: tuyệt đối không trả tên thật hay hồ sơ tác giả.
- Không dùng dữ liệu giả/bịa số liệu; mất kết nối CSDL hoặc chưa cấu hình trả HTTP 503.
- Chạy kết nối trong giao dịch chỉ đọc (conn.read_only = True).
"""

from __future__ import annotations

from datetime import date
import math
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status
import psycopg

from app.core.config import get_settings
from app.schemas.reviews import ReviewItemOut, ReviewsListOut

router = APIRouter(prefix="/api/v1", tags=["Đánh giá"])


def _escape_like(s: str) -> str:
    """Thoát ký tự đại diện trong LIKE / ILIKE: \\, %, _."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _normalize_source(source: str) -> str:
    """Ánh xạ tên hiển thị hoặc mã nguồn về khóa nguồn chuẩn trong dw.dim_source."""
    s = source.strip().lower()
    mapping = {
        "google play": "google_play",
        "google_play": "google_play",
        "app store": "app_store_vn",
        "app store vn": "app_store_vn",
        "app_store": "app_store_vn",
        "app_store_vn": "app_store_vn",
        "youtube": "youtube",
    }
    return mapping.get(s, s)


def _format_source_display(source_name: str | None) -> str:
    """Định dạng nguồn hiển thị thân thiện với người dùng."""
    if not source_name:
        return "Khác"
    mapping = {
        "google_play": "Google Play",
        "app_store_vn": "App Store",
        "youtube": "YouTube",
    }
    return mapping.get(source_name.lower().strip(), source_name)


def _normalize_sentiment(s: str) -> str:
    """Ánh xạ nhãn cảm xúc tìm kiếm về giá trị lưu trong CSDL."""
    cleaned = s.strip().lower()
    mapping = {
        "tích cực": "tich_cuc",
        "tich cuc": "tich_cuc",
        "tich_cuc": "tich_cuc",
        "positive": "tich_cuc",
        "tiêu cực": "tieu_cuc",
        "tieu cuc": "tieu_cuc",
        "tieu_cuc": "tieu_cuc",
        "negative": "tieu_cuc",
        "trung tính": "trung_tinh",
        "trung tinh": "trung_tinh",
        "trung lập": "trung_tinh",
        "trung lap": "trung_tinh",
        "trung_tinh": "trung_tinh",
        "neutral": "trung_tinh",
    }
    return mapping.get(cleaned, cleaned)


def _format_sentiment_display(label: str | None) -> str | None:
    """Định dạng nhãn cảm xúc hiển thị. Trả về None nếu chưa có nhãn mô hình."""
    if not label:
        return None
    cleaned = label.strip().lower()
    if cleaned in ("tich_cuc", "positive", "tích cực", "tich cuc"):
        return "Tích cực"
    if cleaned in ("tieu_cuc", "negative", "tiêu cực", "tieu cuc"):
        return "Tiêu cực"
    if cleaned in ("trung_tinh", "neutral", "trung tính", "trung tinh", "trung lập", "trung lap"):
        return "Trung lập"
    return label


def _check_misaligned_flag(rating: int | None, label: str | None) -> bool:
    """Xác định cờ lệch pha: rating cao mà cảm xúc tiêu cực, hoặc rating thấp mà cảm xúc tích cực."""
    if rating is None or not label:
        return False
    norm = _normalize_sentiment(label)
    if rating >= 4 and norm == "tieu_cuc":
        return True
    if rating <= 2 and norm == "tich_cuc":
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
    """Truy vấn kho dữ liệu PostgreSQL sạch sẽ, an toàn chống SQL injection.
    Toàn bộ bộ lọc chạy trên mức SQL trước khi phân trang.
    """
    with psycopg.connect(database_url, connect_timeout=3) as conn:
        conn.read_only = True
        with conn.cursor() as cur:
            # B4: Kiểm tra bảng cảm xúc mô hình M1 dw.fact_review_sentiment có tồn tại không
            cur.execute("SELECT to_regclass('dw.fact_review_sentiment') IS NOT NULL")
            has_sentiment_table: bool = bool(cur.fetchone()[0])

            # Nếu người dùng muốn lọc cảm xúc hoặc lệch pha nhưng chưa có bảng nhãn mô hình
            if not has_sentiment_table:
                if sentiment and sentiment.strip().lower() != "tất cả cảm xúc":
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Chưa có nhãn cảm xúc từ mô hình",
                    )
                if misaligned_only:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Chưa có nhãn cảm xúc từ mô hình",
                    )

            conditions: list[str] = ["1=1"]
            params: list[Any] = []

            if platform and platform.strip().lower() != "tất cả nền tảng":
                conditions.append("LOWER(p.platform_name) = LOWER(%s)")
                params.append(platform.strip())

            if start_date:
                conditions.append("d.full_date >= %s")
                params.append(start_date)

            if end_date:
                conditions.append("d.full_date <= %s")
                params.append(end_date)

            if rating is not None:
                conditions.append("r.rating = %s")
                params.append(rating)

            if source and source.strip().lower() != "tất cả nguồn":
                norm_src = _normalize_source(source)
                conditions.append("(LOWER(s.source_name) = %s OR LOWER(s.source_name) = LOWER(%s))")
                params.extend([norm_src, source.strip()])

            # B3: Thoát ký tự % và _ trong từ khóa tìm kiếm, chỉ tìm trong nội dung text
            if keyword and keyword.strip():
                kw_escaped = f"%{_escape_like(keyword.strip())}%"
                conditions.append("t.text ILIKE %s ESCAPE '\\'")
                params.append(kw_escaped)

            # B2: Lọc khía cạnh ở mức SQL bằng EXISTS
            if aspect and aspect.strip().lower() != "tất cả khía cạnh":
                conditions.append(
                    "EXISTS ("
                    "  SELECT 1 FROM dw.fact_review_aspect a "
                    "  JOIN dw.dim_aspect da ON da.aspect_key = a.aspect_key "
                    "  WHERE a.review_key = r.review_key AND LOWER(da.aspect_name) = LOWER(%s)"
                    ")"
                )
                params.append(aspect.strip())

            # B4: Lọc cảm xúc và lệch pha ở mức SQL khi bảng M1 đã tồn tại
            if has_sentiment_table:
                if sentiment and sentiment.strip().lower() != "tất cả cảm xúc":
                    norm_st = _normalize_sentiment(sentiment)
                    conditions.append("(LOWER(snt.sentiment_label) = %s OR LOWER(snt.sentiment_label) = LOWER(%s))")
                    params.extend([norm_st, sentiment.strip()])

                if misaligned_only:
                    conditions.append(
                        "((r.rating >= 4 AND LOWER(snt.sentiment_label) IN ('tieu_cuc', 'tiêu cực', 'negative')) "
                        "OR (r.rating <= 2 AND LOWER(snt.sentiment_label) IN ('tich_cuc', 'tích cực', 'positive')))"
                    )

            where_clause = " AND ".join(conditions)

            # Khối JOIN bảng cảm xúc M1
            sentiment_join = (
                "LEFT JOIN dw.fact_review_sentiment snt ON r.review_key = snt.review_key"
                if has_sentiment_table
                else ""
            )

            # Câu lệnh đếm chính xác số lượng thỏa mãn bộ lọc (áp dụng toàn bộ WHERE)
            count_sql = f"""
                SELECT COUNT(r.review_key)
                FROM dw.fact_review r
                JOIN clean.review_text t ON r.review_key = t.review_key
                JOIN dw.dim_platform p ON r.platform_key = p.platform_key
                JOIN dw.dim_time d ON r.time_key = d.time_key
                JOIN dw.dim_source s ON r.source_key = s.source_key
                {sentiment_join}
                WHERE {where_clause}
            """

            cur.execute(count_sql, params)
            total = cur.fetchone()[0]

            offset = (page - 1) * page_size
            data_params = list(params) + [offset, page_size]

            sentiment_select = (
                "snt.sentiment_label, snt.sentiment_score"
                if has_sentiment_table
                else "NULL::text AS sentiment_label, NULL::float AS sentiment_score"
            )

            # Truy vấn lấy dữ liệu trang, không chứa bất kỳ thông tin cá nhân nào (HA2.6)
            data_sql = f"""
                SELECT
                    r.review_key,
                    t.review_id,
                    p.platform_name,
                    s.source_name,
                    r.rating,
                    to_char(d.full_date, 'YYYY-MM-DD') AS created_at,
                    t.text,
                    {sentiment_select},
                    fa.aspect_names
                FROM dw.fact_review r
                JOIN clean.review_text t ON r.review_key = t.review_key
                JOIN dw.dim_platform p ON r.platform_key = p.platform_key
                JOIN dw.dim_time d ON r.time_key = d.time_key
                JOIN dw.dim_source s ON r.source_key = s.source_key
                {sentiment_join}
                LEFT JOIN (
                    SELECT
                        a.review_key,
                        string_agg(da.aspect_name, ', ' ORDER BY da.aspect_name) AS aspect_names
                    FROM dw.fact_review_aspect a
                    JOIN dw.dim_aspect da ON a.aspect_key = da.aspect_key
                    GROUP BY a.review_key
                ) fa ON r.review_key = fa.review_key
                WHERE {where_clause}
                ORDER BY d.full_date DESC, r.review_key DESC
                OFFSET %s LIMIT %s
            """

            cur.execute(data_sql, data_params)
            rows = cur.fetchall()

            items: list[ReviewItemOut] = []
            for row in rows:
                r_key, r_id, p_name, s_name, r_rating, dt_str, txt, s_label, s_score, asp_names = row
                st_display = _format_sentiment_display(s_label)
                misaligned = _check_misaligned_flag(r_rating, s_label)

                aspects_list = [a.strip() for a in asp_names.split(",")] if asp_names else []
                primary_aspect = aspects_list[0] if aspects_list else None

                items.append(
                    ReviewItemOut(
                        review_key=r_key,
                        review_id=r_id,
                        platform=p_name,
                        source=_format_source_display(s_name),
                        rating=r_rating,
                        created_at=dt_str,
                        text=txt,
                        sentiment=st_display,
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
    keyword: Optional[str] = Query(None, description="Từ khóa tìm kiếm trong nội dung đánh giá"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Số sao đánh giá (1-5)"),
    misaligned_only: bool = Query(False, description="Chỉ lấy đánh giá có hiện tượng lệch pha"),
    source: Optional[str] = Query(None, description="Nguồn thu thập"),
    page: int = Query(1, ge=1, description="Số trang hiển thị"),
    page_size: int = Query(20, ge=1, le=100, description="Số lượng bản ghi trên một trang"),
) -> ReviewsListOut:
    """Trả về danh sách đánh giá có phân trang từ kho CSDL PostgreSQL, hỗ trợ bộ lọc đa chiều."""
    settings = get_settings()
    if not settings.database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chưa cấu hình cơ sở dữ liệu",
        )

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
    except psycopg.OperationalError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không kết nối được cơ sở dữ liệu",
        ) from None

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    # HA2.5: Nếu trang yêu cầu vượt quá tổng số trang, trả về danh sách rỗng
    if page > total_pages:
        items = []

    return ReviewsListOut(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items,
    )


@router.get(
    "/reviews/{review_key}",
    response_model=ReviewItemOut,
    summary="Chi tiết một đánh giá theo khóa review_key",
)
def get_review(review_key: int) -> ReviewItemOut:
    """Lấy chi tiết một đánh giá theo khóa số nguyên từ CSDL."""
    settings = get_settings()
    if not settings.database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chưa cấu hình cơ sở dữ liệu",
        )

    try:
        with psycopg.connect(settings.database_url, connect_timeout=3) as conn:
            conn.read_only = True
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass('dw.fact_review_sentiment') IS NOT NULL")
                has_sentiment_table: bool = bool(cur.fetchone()[0])

                sentiment_select = (
                    "snt.sentiment_label, snt.sentiment_score"
                    if has_sentiment_table
                    else "NULL::text AS sentiment_label, NULL::float AS sentiment_score"
                )
                sentiment_join = (
                    "LEFT JOIN dw.fact_review_sentiment snt ON r.review_key = snt.review_key"
                    if has_sentiment_table
                    else ""
                )

                query = f"""
                    SELECT
                        r.review_key,
                        t.review_id,
                        p.platform_name,
                        s.source_name,
                        r.rating,
                        to_char(d.full_date, 'YYYY-MM-DD') AS created_at,
                        t.text,
                        {sentiment_select},
                        fa.aspect_names
                    FROM dw.fact_review r
                    JOIN clean.review_text t ON r.review_key = t.review_key
                    JOIN dw.dim_platform p ON r.platform_key = p.platform_key
                    JOIN dw.dim_time d ON r.time_key = d.time_key
                    JOIN dw.dim_source s ON r.source_key = s.source_key
                    {sentiment_join}
                    LEFT JOIN (
                        SELECT
                            a.review_key,
                            string_agg(da.aspect_name, ', ' ORDER BY da.aspect_name) AS aspect_names
                        FROM dw.fact_review_aspect a
                        JOIN dw.dim_aspect da ON a.aspect_key = da.aspect_key
                        GROUP BY a.review_key
                    ) fa ON r.review_key = fa.review_key
                    WHERE r.review_key = %s
                """
                cur.execute(query, (review_key,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Không tìm thấy đánh giá với mã yêu cầu",
                    )

                r_key, r_id, p_name, s_name, r_rating, dt_str, txt, s_label, s_score, asp_names = row
                st_display = _format_sentiment_display(s_label)
                misaligned = _check_misaligned_flag(r_rating, s_label)

                aspects_list = [a.strip() for a in asp_names.split(",")] if asp_names else []
                primary_aspect = aspects_list[0] if aspects_list else None

                return ReviewItemOut(
                    review_key=r_key,
                    review_id=r_id,
                    platform=p_name,
                    source=_format_source_display(s_name),
                    rating=r_rating,
                    created_at=dt_str,
                    text=txt,
                    sentiment=st_display,
                    sentiment_score=float(s_score) if s_score is not None else None,
                    aspect=primary_aspect,
                    aspects=aspects_list,
                    misaligned=misaligned,
                )
    except psycopg.OperationalError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không kết nối được cơ sở dữ liệu",
        ) from None
