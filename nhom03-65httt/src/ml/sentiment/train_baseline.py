"""E1 (mô hình nền): TF-IDF + Logistic Regression cho cảm xúc 3 lớp. Chạy từ thư mục nhom03-65httt:

    python src/ml/sentiment/train_baseline.py [--save models/m1_tfidf_lr/model.joblib]

In macro-F1 trên: tập kiểm thử (10% mẫu huấn luyện), tập vàng LLM (1.200, trừ bo_qua) và chéo nền tảng
(huấn luyện nhóm trong nước, kiểm thử nhóm quốc tế và ngược lại).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import LABELS, ROOT, label_counts, load_gold, load_train, metrics, split_stratified  # noqa: E402


def build_pipeline(C: float = 4.0):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import FeatureUnion, Pipeline
    features = FeatureUnion([
        ("word", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ("char", TfidfVectorizer(lowercase=True, analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True)),
    ])
    return Pipeline([("tfidf", features),
                     ("lr", LogisticRegression(C=C, max_iter=2000, class_weight="balanced"))])


def fit_eval(train_rows, test_rows, C: float = 4.0):
    model = build_pipeline(C)
    model.fit([r["text"] for r in train_rows], [r["y"] for r in train_rows])
    pred = model.predict([r["text"] for r in test_rows])
    return model, metrics([r["y"] for r in test_rows], list(pred))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="E1: TF-IDF + Logistic Regression (mô hình nền M1)")
    parser.add_argument("--save", type=Path, help="lưu mô hình (joblib) vào đường dẫn này")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "ml" / "e1_tfidf_lr.json")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    rows = load_train()
    gold = load_gold()
    train, val, test = split_stratified(rows)
    print(f"mẫu huấn luyện dùng được: {len(rows)} {label_counts(rows)} | chia {len(train)}/{len(val)}/{len(test)} | vàng {len(gold)}")

    # chọn C bằng tập validation (không đụng tới test và vàng)
    best_c, best_f1 = None, -1.0
    for c in (0.5, 1.0, 2.0, 4.0, 8.0, 16.0):
        _, m = fit_eval(train, val, c)
        print(f"  C={c:<5} macro-F1 validation = {m['macro_f1']}")
        if m["macro_f1"] > best_f1:
            best_c, best_f1 = c, m["macro_f1"]
    model, test_m = fit_eval(train, test, best_c)
    gold_m = metrics([r["y"] for r in gold], list(model.predict([r["text"] for r in gold])))

    cross = {}
    for src, dst in (("trong_nuoc", "quoc_te"), ("quoc_te", "trong_nuoc")):
        a = [r for r in rows if r["group"] == src]
        b = [r for r in rows if r["group"] == dst]
        _, cm = fit_eval(a, b, best_c)
        cross[f"{src}->{dst}"] = cm

    result = {"model": "tfidf_lr", "C": best_c, "validation_macro_f1": best_f1, "test": test_m, "gold_llm": gold_m, "cross_platform": cross}
    print(json.dumps({k: (v if k not in ("test", "gold_llm", "cross_platform") else None) for k, v in result.items()}, ensure_ascii=False))
    print(f"TEST   macro-F1 = {test_m['macro_f1']}  accuracy = {test_m['accuracy']}  F1/lớp = {test_m['f1_per_class']}")
    print(f"VÀNG   macro-F1 = {gold_m['macro_f1']}  accuracy = {gold_m['accuracy']}  F1/lớp = {gold_m['f1_per_class']}")
    for name, m in cross.items():
        print(f"CHÉO {name}: macro-F1 = {m['macro_f1']} (n={m['n']})")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.save:
        import joblib
        args.save.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": model, "labels": LABELS}, args.save)
        print("đã lưu mô hình:", args.save)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
