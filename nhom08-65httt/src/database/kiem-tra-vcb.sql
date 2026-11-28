-- Chạy trong database cafeflow sau khi đã collect_vcb ít nhất một lần.
-- Ba truy vấn đầu phải trả về 0 dòng: không trùng revision/không có nhiều
-- revision hiện hành cho cùng nguồn, ngoại tệ, loại tỷ giá và thời điểm.
SELECT source_id, currency_code, rate_type, effective_at, revision, COUNT(*) AS duplicate_count
FROM dw_fx_observation
GROUP BY source_id, currency_code, rate_type, effective_at, revision
HAVING COUNT(*) > 1;

SELECT source_id, currency_code, rate_type, effective_at, COUNT(*) AS current_count
FROM dw_fx_observation
WHERE is_current
GROUP BY source_id, currency_code, rate_type, effective_at
HAVING COUNT(*) > 1;

SELECT currency_code, rate_type, effective_at, COUNT(*) AS current_revision_count
FROM dw_fx_observation
WHERE is_current
GROUP BY currency_code, rate_type, effective_at
HAVING COUNT(*) > 1;

-- Đối chiếu số quan sát theo nguồn và lần thu thập.
SELECT r.id AS run_id, r.status, r.collected_at, r.rows_received,
       r.created_count, r.revised_count, r.unchanged_count, r.rejected_count,
       COUNT(o.id) AS stored_observations
FROM raw_collection_run AS r
JOIN market_source AS s ON s.id = r.source_id AND s.code = 'vietcombank'
LEFT JOIN dw_fx_observation AS o ON o.run_id = r.id
GROUP BY r.id
ORDER BY r.id DESC
LIMIT 10;

-- Một bản hiện hành mới nhất cho mỗi ngoại tệ và loại tỷ giá.
SELECT DISTINCT ON (currency_code, rate_type)
       currency_code, currency_name, rate_type, value, effective_at, revision
FROM dw_fx_observation
WHERE source_id = (SELECT id FROM market_source WHERE code = 'vietcombank')
  AND is_current
ORDER BY currency_code, rate_type, effective_at DESC, id DESC;
