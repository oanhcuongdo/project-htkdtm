-- Đối chiếu trạng thái HTTP, số ngày trong PDF và số quan sát của từng lần chạy.
SELECT r.id, r.status, r.http_status, r.source_url, r.collected_at,
       r.rows_received, r.rejected_count, r.created_count, r.revised_count,
       r.unchanged_count, r.error, d.content_hash, octet_length(d.payload) AS raw_bytes
FROM raw_collection_run AS r
JOIN market_source AS s ON s.id = r.source_id
LEFT JOIN raw_document AS d ON d.id = r.raw_document_id
WHERE s.code = 'ico'
ORDER BY r.id DESC;

-- Bản giá hiện hành có cùng ngày, nguồn và đơn vị như API.
SELECT s.code AS source, series.code AS series, o.effective_date, o.value,
       series.unit, o.revision, r.id AS collection_run, r.source_url, r.collected_at
FROM dw_price_observation AS o
JOIN dw_price_series AS series ON series.id = o.series_id
JOIN market_source AS s ON s.id = series.source_id
JOIN raw_collection_run AS r ON r.id = o.run_id
WHERE s.code = 'ico' AND series.code = 'robustas' AND o.is_current
ORDER BY o.effective_date DESC
LIMIT 5;
