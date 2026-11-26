"""Kiểm thử phần mã M1 không cần tải PhoBERT: đọc dữ liệu, chia tập, số đo, gom lô và ghi nhãn vào CSDL."""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

SENTIMENT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SENTIMENT_DIR))

import sentiment_common as common  # noqa: E402
from phobert_model import length_buckets  # noqa: E402


def _write(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


@pytest.fixture()
def label_dir(tmp_path):
    sample = [["T1", "google_play", "a", "DUOLINGO", "5", "rất tốt"], ["T2", "google_play", "b", "VUIHOC", "1", "tệ quá"],
              ["T3", "youtube", "c", "VUIHOC", "", "tạm được"], ["T4", "google_play", "d", "Busuu", "3", "không rõ"]]
    _write(tmp_path / "training_sample_4000.csv", ["item_id", "source", "review_id", "platform", "rating", "text"], sample)
    labels = [["T1", "google_play", "a", "DUOLINGO", "tich_cuc", "", "", "", ""],
              ["T2", "google_play", "b", "VUIHOC", "tieu_cuc", "", "", "", ""],
              ["T3", "youtube", "c", "VUIHOC", "trung_tinh", "", "", "", ""],
              ["T4", "google_play", "d", "Busuu", "bo_qua", "", "", "", ""]]
    _write(tmp_path / "llm_labels_train.csv",
           ["item_id", "source", "review_id", "platform", "sentiment", "technical", "academic", "customer_service", "pricing"], labels)
    _write(tmp_path / "gold_texts_1200.csv", ["item_id", "text"], [["G1", "hay"], ["G2", "dở"], ["G3", "?"]])
    _write(tmp_path / "llm_labels_gold.csv", ["item_id", "sentiment", "technical", "academic", "customer_service", "pricing"],
           [["G1", "tich_cuc", "", "", "", ""], ["G2", "tieu_cuc", "", "", "", ""], ["G3", "bo_qua", "", "", "", ""]])
    return tmp_path


def test_load_train_drops_bo_qua_and_maps_labels_and_groups(label_dir):
    rows = common.load_train(label_dir)
    assert [r["item_id"] for r in rows] == ["T1", "T2", "T3"]           # T4 là bo_qua nên bị loại
    by_id = {r["item_id"]: r for r in rows}
    assert by_id["T1"]["y"] == common.LABEL_TO_ID["tich_cuc"] == 2
    assert by_id["T2"]["y"] == 0 and by_id["T3"]["y"] == 1
    assert by_id["T1"]["group"] == "quoc_te" and by_id["T2"]["group"] == "trong_nuoc"


def test_load_gold_drops_bo_qua(label_dir):
    assert [r["item_id"] for r in common.load_gold(label_dir)] == ["G1", "G2"]


def _fake_rows(n_each=50):
    return [{"item_id": f"{lab}{i:03d}", "label": lab, "y": common.LABEL_TO_ID[lab], "text": "x"}
            for lab in common.LABELS for i in range(n_each)]


def test_split_is_disjoint_complete_stratified_and_deterministic():
    rows = _fake_rows(50)
    train, val, test = common.split_stratified(rows)
    ids = [r["item_id"] for r in train + val + test]
    assert len(ids) == len(set(ids)) == len(rows)                       # không trùng, không mất
    assert (len(train), len(val), len(test)) == (120, 15, 15)
    for part in (train, val, test):                                      # mỗi tập đều đủ ba lớp, tỷ lệ đều
        counts = common.label_counts(part)
        assert max(counts.values()) - min(counts.values()) <= 1
    again = common.split_stratified(rows)
    assert [r["item_id"] for r in again[2]] == [r["item_id"] for r in test]


def test_split_rejects_bad_fractions():
    with pytest.raises(ValueError):
        common.split_stratified(_fake_rows(5), fractions=(0.5, 0.1, 0.1))


def test_metrics_macro_f1_perfect_and_worst_case():
    perfect = common.metrics([0, 1, 2, 2], [0, 1, 2, 2])
    assert perfect["macro_f1"] == 1.0 and perfect["accuracy"] == 1.0
    assert perfect["confusion"] == [[1, 0, 0], [0, 1, 0], [0, 0, 2]]
    worst = common.metrics([0, 1, 2], [1, 2, 0])
    assert worst["macro_f1"] == 0.0
    only_majority = common.metrics([0, 0, 0, 1, 2], [0] * 5)           # đoán một lớp: macro-F1 thấp dù accuracy 60%
    assert only_majority["accuracy"] == 0.6 and only_majority["macro_f1"] < 0.4


def test_length_buckets_cover_every_index_once_and_group_similar_lengths():
    lengths = [3, 90, 4, 88, 5, 91, 2, 87]
    batches = length_buckets(lengths, 4)
    flat = [i for b in batches for i in b]
    assert sorted(flat) == list(range(len(lengths)))
    assert [sorted(lengths[i] for i in b) for b in batches] == [[2, 3, 4, 5], [87, 88, 90, 91]]
    shuffled = length_buckets(lengths, 4, shuffle_seed=7)
    assert sorted(i for b in shuffled for i in b) == list(range(len(lengths)))
    assert shuffled == length_buckets(lengths, 4, shuffle_seed=7)       # cùng hạt, cùng kết quả


# ---- ghi nhãn vào CSDL (cần PostgreSQL đã có migration 0004; không thì bỏ qua) ----
def _score_all():
    spec = importlib.util.spec_from_file_location("m1_score_all", SENTIMENT_DIR / "score_all.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def conn():
    spec = importlib.util.spec_from_file_location("etl_common_t", common.ROOT / "src" / "etl" / "common.py")
    etl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(etl)
    try:
        connection = etl.connect(connect_timeout=3)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Không kết nối được PostgreSQL cục bộ: {type(exc).__name__}")
    with connection.cursor() as cur:
        cur.execute("SELECT to_regclass('dw.fact_review_sentiment') IS NOT NULL")
        if not cur.fetchone()[0]:
            connection.close()
            pytest.skip("Chưa chạy migration 0004 (thiếu dw.fact_review_sentiment)")
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


def test_upsert_maps_probabilities_and_is_idempotent(conn):
    module = _score_all()
    with conn.cursor() as cur:
        cur.execute("SELECT review_key FROM dw.fact_review ORDER BY review_key LIMIT 3")
        keys = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT model_key FROM dw.dim_model WHERE model_name = 'M1_phobert'")
        model_key = cur.fetchone()[0]
        cur.execute("DELETE FROM dw.fact_review_sentiment WHERE review_key = ANY(%s)", (keys,))
    if len(keys) < 3:
        pytest.skip("Kho chưa đủ 3 đánh giá")
    proba = np.array([[0.1, 0.2, 0.7], [0.8, 0.1, 0.1], [0.3, 0.4, 0.3]], dtype=np.float32)   # thứ tự: tieu_cuc, trung_tinh, tich_cuc
    module.upsert_rows(conn, model_key, keys, proba)
    module.upsert_rows(conn, model_key, keys, proba)                    # chạy lại không sinh dòng trùng
    with conn.cursor() as cur:
        cur.execute("SELECT review_key, sentiment_label, sentiment_score, confidence FROM dw.fact_review_sentiment "
                    "WHERE review_key = ANY(%s) ORDER BY review_key", (keys,))
        got = cur.fetchall()
    assert [g[1] for g in got] == ["tich_cuc", "tieu_cuc", "trung_tinh"]
    assert [float(g[2]) for g in got] == pytest.approx([0.6, -0.7, 0.0], abs=1e-3)   # P(tích cực) - P(tiêu cực)
    assert [float(g[3]) for g in got] == pytest.approx([0.7, 0.8, 0.4], abs=1e-3)


def test_fetch_pending_skips_already_scored(conn):
    module = _score_all()
    with conn.cursor() as cur:
        cur.execute("SELECT model_key FROM dw.dim_model WHERE model_name = 'M1_phobert'")
        model_key = cur.fetchone()[0]
        cur.execute("DELETE FROM dw.fact_review_sentiment")
    first = module.fetch_pending(conn, model_key, rescore=False, lang="all", limit=5)
    assert len(first) == 5
    module.upsert_rows(conn, model_key, [k for k, _ in first], np.tile([0.2, 0.2, 0.6], (5, 1)).astype(np.float32))
    after = module.fetch_pending(conn, model_key, rescore=False, lang="all", limit=5)
    assert not ({k for k, _ in first} & {k for k, _ in after})          # phần đã chấm không bị chấm lại
    again = module.fetch_pending(conn, model_key, rescore=True, lang="all", limit=5)
    assert {k for k, _ in first} == {k for k, _ in again}               # rescore thì lấy lại từ đầu
