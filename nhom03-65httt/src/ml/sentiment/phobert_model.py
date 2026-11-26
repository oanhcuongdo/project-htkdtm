"""M1 PhoBERT: tách từ, mã hóa theo lô gom theo độ dài và dự đoán xác suất. Dùng cho huấn luyện lẫn chấm điểm toàn kho.

PhoBERT (vinai/phobert-base-v2) được huấn luyện trên văn bản đã TÁCH TỪ (từ ghép nối bằng dấu gạch dưới), nên mọi văn bản
đưa vào, lúc huấn luyện hay lúc chấm điểm, đều qua `segment` giống nhau.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

BASE_MODEL = "vinai/phobert-base-v2"
MAX_LEN = 128


@lru_cache(maxsize=200_000)
def segment(text: str) -> str:
    """Tách từ tiếng Việt bằng underthesea; lỗi hoặc rỗng thì trả về văn bản gốc."""
    from underthesea import word_tokenize
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return ""
    try:
        return word_tokenize(cleaned, format="text")
    except Exception:  # noqa: BLE001 - một văn bản lạ không được làm hỏng cả lô
        return cleaned


def length_buckets(lengths: Sequence[int], batch_size: int, shuffle_seed: int | None = None) -> list[list[int]]:
    """Chia chỉ số thành các lô có độ dài gần nhau (ít đệm, chạy nhanh trên CPU). Có hạt thì xáo trộn thứ tự lô."""
    rng = np.random.default_rng(shuffle_seed) if shuffle_seed is not None else None
    order = list(range(len(lengths)))
    if rng is not None:
        rng.shuffle(order)
        chunk = batch_size * 50
        chunks = [sorted(order[i:i + chunk], key=lambda k: lengths[k]) for i in range(0, len(order), chunk)]
    else:
        chunks = [sorted(order, key=lambda k: lengths[k])]
    batches = [c[i:i + batch_size] for c in chunks for i in range(0, len(c), batch_size)]
    if rng is not None:
        rng.shuffle(batches)
    return batches


class Scorer:
    """Nạp mô hình đã huấn luyện (thư mục save_pretrained) và dự đoán xác suất ba lớp theo thứ tự common.LABELS."""

    def __init__(self, model_dir: str | Path | None = None, threads: int | None = None):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        if threads:
            torch.set_num_threads(threads)
        source = str(model_dir) if model_dir else BASE_MODEL
        self.tokenizer = AutoTokenizer.from_pretrained(source if model_dir else BASE_MODEL)
        self.model = AutoModelForSequenceClassification.from_pretrained(source, num_labels=3)
        self.model.eval()
        self.torch = torch

    def encode(self, texts: Sequence[str]):
        return self.tokenizer([segment(t) for t in texts], padding=True, truncation=True,
                              max_length=MAX_LEN, return_tensors="pt")

    def predict_proba(self, texts: Sequence[str], batch_size: int = 64, progress=None) -> np.ndarray:
        """Trả về mảng (n, 3) xác suất, đúng thứ tự đầu vào."""
        texts = list(texts)
        lengths = [len(t.split()) for t in texts]
        out = np.zeros((len(texts), 3), dtype=np.float32)
        done = 0
        with self.torch.no_grad():
            for idx in length_buckets(lengths, batch_size):
                enc = self.encode([texts[i] for i in idx])
                logits = self.model(**enc).logits
                out[idx] = self.torch.softmax(logits, dim=-1).numpy()
                done += len(idx)
                if progress:
                    progress(done, len(texts))
        return out


def save_model(model, tokenizer, directory: Path, info: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(directory)
    tokenizer.save_pretrained(directory)
    (directory / "m1_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
