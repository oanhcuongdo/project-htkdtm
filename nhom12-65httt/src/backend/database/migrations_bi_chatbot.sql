-- ==============================================================================
-- MIGRATIONS GÓI 2: BI, CHATBOT TEXT-TO-SQL (RBAC + READ ONLY) & QUẢN TRỊ RỦI RO
-- Hệ thống Tìm kiếm Nhà thuê Thông minh (Hà Nội) - Nhóm 12 (65HTTT)
-- ==============================================================================

-- 1. VIEW RBAC CHO CHATBOT: VAI TRÒ NGƯỜI THUÊ (RENTER)
-- Chỉ hiển thị tin đang hoạt động (is_active = true) và không trùng lặp (is_duplicate = false).
-- Ẩn các cột nhạy cảm/quản trị (risk_score, thông tin người đăng chi tiết, báo cáo vi phạm).
CREATE OR REPLACE VIEW public.view_chatbot_renter_listings AS
SELECT
    f.fact_id,
    f.source,
    f.title,
    f.price,
    f.area,
    f.price_per_m2,
    f.deposit_amount,
    f.electricity_cost,
    f.water_cost,
    f.service_cost,
    f.estimated_total_cost,
    f.price_diff_rate,
    f.price_segment,
    f.completeness_score,
    f.room_status,
    f.created_at,
    t.full_date,
    t.month,
    t.month_name,
    t.quarter,
    t.year,
    t.is_peak_student_season,
    l.district,
    l.ward,
    l.street,
    l.nearest_university,
    l.distance_to_university_km,
    pt.type_code,
    pt.type_name,
    a.has_air_conditioner,
    a.has_water_heater,
    a.has_washing_machine,
    a.has_private_bathroom,
    a.has_kitchen,
    a.has_balcony,
    a.has_elevator,
    a.has_parking,
    a.has_security,
    a.has_flexible_hours,
    ll.poster_type
FROM public.fact_rental_listings f
LEFT JOIN public.dim_time t ON f.time_id = t.time_id
LEFT JOIN public.dim_location l ON f.location_id = l.location_id
LEFT JOIN public.dim_property_type pt ON f.property_type_id = pt.property_type_id
LEFT JOIN public.dim_amenities a ON f.amenity_id = a.amenity_id
LEFT JOIN public.dim_landlord ll ON f.landlord_id = ll.landlord_id
WHERE f.is_active = true
  AND COALESCE(f.is_duplicate, false) = false;

-- 2. VIEW RBAC CHO CHATBOT: VAI TRÒ QUẢN TRỊ VIÊN (ADMIN)
-- Cho phép truy vấn toàn bộ tin (kể cả tin đã ẩn/trùng lặp), điểm rủi ro, độ tin cậy và số báo cáo vi phạm.
CREATE OR REPLACE VIEW public.view_chatbot_admin_analytics AS
SELECT
    v.*,
    COALESCE(rep.report_count, 0) AS report_count,
    COALESCE(rep.pending_report_count, 0) AS pending_report_count
FROM public.view_rental_market_analytics v
LEFT JOIN (
    SELECT
        fact_id,
        COUNT(*)::INT AS report_count,
        COUNT(*) FILTER (WHERE status = 'pending')::INT AS pending_report_count
    FROM public.listing_reports
    GROUP BY fact_id
) rep ON v.fact_id = rep.fact_id;

-- 3. HÀM RPC THỰC THI TRUY VẤN BI AN TOÀN (READ ONLY + STATEMENT TIMEOUT 5000ms)
-- Chỉ chấp nhận 1 câu SELECT duy nhất, ép transaction READ ONLY và timeout 5000ms.
CREATE OR REPLACE FUNCTION public.execute_readonly_bi_query(sql_query TEXT)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    cleaned_sql TEXT;
    result_json JSONB;
BEGIN
    cleaned_sql := btrim(COALESCE(sql_query, ''));
    -- Bỏ dấu chấm phẩy ở cuối nếu có
    cleaned_sql := regexp_replace(cleaned_sql, ';+\s*$', '');

    IF cleaned_sql = '' THEN
        RAISE EXCEPTION 'Câu truy vấn không được để trống.';
    END IF;

    -- Không cho phép nhiều câu lệnh ngăn cách bởi dấu chấm phẩy
    IF cleaned_sql ~ ';' THEN
        RAISE EXCEPTION 'Chỉ cho phép thực thi đúng 1 câu SELECT.';
    END IF;

    -- Chỉ cho phép bắt đầu bằng SELECT hoặc WITH (CTE)
    IF cleaned_sql !~* '^(SELECT|WITH)\s+' THEN
        RAISE EXCEPTION 'Chỉ cho phép câu lệnh SELECT.';
    END IF;

    -- Chặn các từ khóa thay đổi dữ liệu hoặc thao tác hệ thống
    IF cleaned_sql ~* '\y(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|COPY|EXECUTE|CALL|DO|VACUUM|ANALYZE)\y' THEN
        RAISE EXCEPTION 'Phát hiện từ khóa không được phép trong truy vấn chỉ đọc.';
    END IF;

    -- Ép chế độ chỉ đọc và giới hạn thời gian thực thi 5000ms trong transaction hiện tại
    PERFORM set_config('default_transaction_read_only', 'on', true);
    PERFORM set_config('statement_timeout', '5000', true);

    EXECUTE format(
        'SELECT COALESCE(jsonb_agg(row_to_json(sub)), ''[]''::jsonb) FROM (%s) AS sub',
        cleaned_sql
    )
    INTO result_json;

    RETURN COALESCE(result_json, '[]'::jsonb);
END;
$$;

REVOKE ALL ON FUNCTION public.execute_readonly_bi_query(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.execute_readonly_bi_query(TEXT) TO anon, authenticated, service_role;
