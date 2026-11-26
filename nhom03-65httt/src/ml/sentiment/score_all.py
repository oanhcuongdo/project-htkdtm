"""Chấm điểm cảm xúc M1 cho đánh giá trong kho và ghi vào dw.fact_review_sentiment (mỗi đánh giá một dòng, giữ kết quả mới nhất).

Cần migration 0004 (bảng dw.fact_review_sentiment, dw.etl_run_log, dw.dim_model đã có 'M1_phobert'). Chạy từ nhom03-65httt:

    python src/ml/sentiment/score_all.py --dry-run --limit 500     # thử: tính, in phân bố, hoàn tác
    python src/ml/sentiment/score_all.py                           # chấm các đánh giá CHƯA có nhãn của mô hình này
    python src/ml/sentiment/score_all.py --rescore                 # chấm lại tất cả (sau khi huấn luyện lại)
    python src/ml/sentiment/score_all.py --lang vi                 # chỉ chấm văn bản nhận dạng là tiếng Việt

Ghi theo lô và commit từng lô nên dừng giữa chừng rồi chạy lại sẽ tiếp tục, không chấm lại phần đã xong.
sentiment_score = P(tích cực) - P(tiêu cực) (thang -1 đến 1); confidence = xác suất cao nhất.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sentiment_common import LABELS, ROOT  # noqa: E402  (common của ML; ETL cũng có common.py nên nạp bản ETL theo tên riêng)

MODEL_NAME, MODEL_VERSION = "M1_phobert", "v0"
DEFAULT_MODEL_DIR = ROOT / "models" / "m1_phobert_sentiment"


def _etl_connect():
    spec = importlib.util.spec_from_file_location("etl_common", ROOT / "src" / "etl" / "common.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.connect


def fetch_pending(conn, model_key: int, rescore: bool, lang: str, limit: int) -> list[tuple[int, str]]:
    """Các (review_key, văn bản) cần chấm. Không rescore thì bỏ qua đánh giá đã có nhãn của chính mô hình này."""
    where, params = ["c.text IS NOT NULL", "btrim(c.text) <> ''"], []
    if lang != "all":
        where.append("c.lang_guess = %s")
        params.append(lang)
    if not rescore:
        where.append("NOT EXISTS (SELECT 1 FROM dw.fact_review_sentiment s WHERE s.review_key = f.review_key AND s.model_key = %s)")
        params.append(model_key)
    sql = ("SELECT f.review_key, c.text FROM dw.fact_review f JOIN clean.review_text c USING (review_key) WHERE "
           + " AND ".join(where) + " ORDER BY f.review_key" + (f" LIMIT {int(limit)}" if limit else ""))
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def upsert_rows(conn, model_key: int, review_keys: list[int], proba) -> None:
    rows = []
    for key, p in zip(review_keys, proba):
        top = int(p.argmax())
        rows.append((key, model_key, LABELS[top], round(float(p[2] - p[0]), 3), round(float(p[top]), 3)))
    with conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO dw.fact_review_sentiment (review_key, model_key, sentiment_label, sentiment_score, confidence, scored_at)
               VALUES (%s, %s, %s, %s, %s, now())
               ON CONFLICT (review_key) DO UPDATE SET model_key = EXCLUDED.model_key,
                   sentiment_label = EXCLUDED.sentiment_label, sentiment_score = EXCLUDED.sentiment_score,
                   confidence = EXCLUDED.confidence, scored_at = EXCLUDED.scored_at""", rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Chấm điểm cảm xúc M1 vào dw.fact_review_sentiment")
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--lang", choices=("all", "vi", "other"), default="all", help="lọc theo clean.review_text.lang_guess")
    parser.add_argument("--limit", type=int, default=0, help="chỉ chấm N đánh giá đầu (thử nhanh)")
    parser.add_argument("--rescore", action="store_true", help="chấm lại cả đánh giá đã có nhãn")
    parser.add_argument("--dry-run", action="store_true", help="tính và in phân bố rồi hoàn tác, không ghi")
    parser.add_argument("--chunk", type=int, default=1000, help="số đánh giá mỗi lần commit")
    parser.add_argument("--threads", type=int, default=16)
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    connect = _etl_connect()
    from phobert_model import Scorer
    started_at = datetime.now(timezone.utc)
    t0 = time.monotonic()
    run_id = "score-" + started_at.strftime("%Y%m%dT%H%M%SZ")
    status, error, total_read, total_written = "success", None, 0, 0
    dist: Counter = Counter()

    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT model_key FROM dw.dim_model WHERE model_name = %s AND model_version = %s",
                        (MODEL_NAME, MODEL_VERSION))
            found = cur.fetchone()
            if not found or conn.execute("SELECT to_regclass('dw.fact_review_sentiment')").fetchone()[0] is None:
                print("LỖI: chưa có migration 0004 (dw.fact_review_sentiment hoặc dim_model 'M1_phobert').", file=sys.stderr)
                return 2
            model_key = found[0]
        pending = fetch_pending(conn, model_key, args.rescore, args.lang, args.limit)
        total_read = len(pending)
        print(f"cần chấm: {total_read} đánh giá (lang={args.lang}, rescore={args.rescore}, dry_run={args.dry_run})", flush=True)
        scorer = Scorer(args.model_dir, args.threads)
        try:
            for start in range(0, total_read, args.chunk):
                part = pending[start:start + args.chunk]
                proba = scorer.predict_proba([t for _, t in part])
                upsert_rows(conn, model_key, [k for k, _ in part], proba)
                dist.update(LABELS[int(i)] for i in proba.argmax(1))
                total_written += len(part)
                if not args.dry_run:
                    conn.commit()
                print(f"  {total_written}/{total_read} ({(time.monotonic() - t0) / 60:.1f} phút)", flush=True)
        except Exception as exc:  # noqa: BLE001 - ghi nhật ký rồi báo lỗi, phần đã commit vẫn giữ
            conn.rollback()
            status, error = "failed", f"{type(exc).__name__}: {exc}"
        if args.dry_run:
            conn.rollback()
            status = "dry_run" if status == "success" else status
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO dw.etl_run_log (run_id, step, started_at, finished_at, status, input_name,
                                               rows_read, rows_inserted, rows_dropped, error_message)
                   VALUES (%s, 'score', %s, now(), %s, %s, %s, %s, %s, %s)""",
                (run_id, started_at, status, f"{MODEL_NAME}:{args.model_dir.name}", total_read, total_written,
                 total_read - total_written, error))
        conn.commit()

    print(f"trạng thái: {status}" + (f" ({error})" if error else ""))
    print("phân bố nhãn vừa chấm:", {k: dist.get(k, 0) for k in LABELS}, f"| tổng {sum(dist.values())}")
    return 0 if status in ("success", "dry_run") else 1


if __name__ == "__main__":
    raise SystemExit(main())
