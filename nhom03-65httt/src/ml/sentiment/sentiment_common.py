"""M1 (cảm xúc 3 lớp): đọc dữ liệu gán nhãn, chia tập, đo macro-F1. Dùng chung cho mô hình nền, PhoBERT và chấm điểm.

Dữ liệu (NGOÀI Git, data/raw/labeling/):
  - training_sample_4000.csv + llm_labels_train.csv: 4.000 đánh giá tiếng Việt, nhãn do LLM gán theo RUBRIC.
  - gold_texts_1200.csv + llm_labels_gold.csv: tập vàng, nhãn LLM; KHÔNG dùng để huấn luyện, chỉ để đo.
Nhãn `bo_qua` (không đủ thông tin) bị loại. Nhãn LLM không phải nhãn người: khi có BoGanNhan của nhóm thì đo lại.
"""

from __future__ import annotations

import csv
import random
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]                 # thư mục nhom03-65httt
LABEL_DIR = ROOT / "data" / "raw" / "labeling"
LABELS = ["tieu_cuc", "trung_tinh", "tich_cuc"]            # thứ tự lớp cố định: chỉ số 0, 1, 2
LABEL_TO_ID = {name: i for i, name in enumerate(LABELS)}
SEED = 42

csv.field_size_limit(10**9)


def _read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def platform_groups() -> dict[str, str]:
    data = yaml.safe_load((ROOT / "config" / "platforms.yml").read_text(encoding="utf-8"))
    return {p["id"]: p["platform_group"] for p in data["platforms"]}


def load_train(label_dir: Path = LABEL_DIR) -> list[dict]:
    """Mẫu huấn luyện: item_id, text, label (chuỗi), y (số), platform, group, source."""
    sample = {r["item_id"]: r for r in _read(label_dir / "training_sample_4000.csv")}
    groups = platform_groups()
    rows = []
    for lab in _read(label_dir / "llm_labels_train.csv"):
        if lab["sentiment"] not in LABEL_TO_ID:
            continue                                        # bo_qua
        s = sample[lab["item_id"]]
        rows.append({"item_id": lab["item_id"], "text": s["text"], "label": lab["sentiment"],
                     "y": LABEL_TO_ID[lab["sentiment"]], "platform": s["platform"],
                     "group": groups.get(s["platform"], "khac"), "source": s["source"]})
    return rows


def load_gold(label_dir: Path = LABEL_DIR) -> list[dict]:
    texts = {r["item_id"]: r["text"] for r in _read(label_dir / "gold_texts_1200.csv")}
    rows = []
    for lab in _read(label_dir / "llm_labels_gold.csv"):
        if lab["sentiment"] not in LABEL_TO_ID:
            continue
        rows.append({"item_id": lab["item_id"], "text": texts[lab["item_id"]], "label": lab["sentiment"],
                     "y": LABEL_TO_ID[lab["sentiment"]]})
    return rows


def split_stratified(rows: list[dict], seed: int = SEED, fractions=(0.8, 0.1, 0.1)) -> tuple[list, list, list]:
    """Chia train/validation/test, giữ tỷ lệ nhãn; cùng hạt ngẫu nhiên cho cùng kết quả."""
    if abs(sum(fractions) - 1) > 1e-9:
        raise ValueError("tổng tỷ lệ phải bằng 1")
    rng = random.Random(seed)
    by_label: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_label[row["label"]].append(row)
    train, val, test = [], [], []
    for label in sorted(by_label):
        items = sorted(by_label[label], key=lambda r: r["item_id"])
        rng.shuffle(items)
        n_train = round(len(items) * fractions[0])
        n_val = round(len(items) * fractions[1])
        train += items[:n_train]
        val += items[n_train:n_train + n_val]
        test += items[n_train + n_val:]
    return train, val, test


def metrics(y_true: list[int], y_pred: list[int]) -> dict:
    """Macro-F1, độ chính xác, F1 từng lớp và ma trận nhầm lẫn (hàng = thật, cột = dự đoán)."""
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
    return {
        "n": len(y_true),
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro", labels=[0, 1, 2], zero_division=0)), 4),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "f1_per_class": {LABELS[i]: round(float(v), 4) for i, v in enumerate(
            f1_score(y_true, y_pred, average=None, labels=[0, 1, 2], zero_division=0))},
        "confusion": confusion_matrix(y_true, y_pred, labels=[0, 1, 2]).tolist(),
    }


def label_counts(rows: list[dict]) -> dict[str, int]:
    return dict(Counter(r["label"] for r in rows))
