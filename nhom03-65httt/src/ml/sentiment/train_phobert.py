"""Huấn luyện M1: tinh chỉnh PhoBERT (vinai/phobert-base-v2) cho cảm xúc 3 lớp trên nhãn LLM. Chạy từ nhom03-65httt:

    python src/ml/sentiment/train_phobert.py [--epochs 4] [--batch-size 32] [--lr 3e-5]

Chọn epoch tốt nhất bằng macro-F1 trên tập validation; test và tập vàng chỉ đo MỘT lần ở cuối.
Trọng số lưu ở models/m1_phobert_sentiment/ (ngoài Git). Kết quả đo ở data/ml/e1_phobert.json.
Chạy trên CPU: khoảng 30 đến 60 phút cho 4 epoch với ~3.000 mẫu.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sentiment_common import LABELS, ROOT, SEED, label_counts, load_gold, load_train, metrics, split_stratified  # noqa: E402
from phobert_model import BASE_MODEL, MAX_LEN, Scorer, length_buckets, save_model, segment  # noqa: E402


def say(*parts) -> None:
    print(time.strftime("%H:%M:%S"), *parts, flush=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Huấn luyện M1 PhoBERT (cảm xúc 3 lớp)")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--threads", type=int, default=16)
    parser.add_argument("--limit", type=int, default=0, help="chỉ dùng N mẫu huấn luyện (chạy thử nhanh)")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "models" / "m1_phobert_sentiment")
    parser.add_argument("--report", type=Path, default=ROOT / "data" / "ml" / "e1_phobert.json")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    import torch
    from transformers import get_linear_schedule_with_warmup
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
    torch.set_num_threads(args.threads)

    rows = load_train()
    gold = load_gold()
    train, val, test = split_stratified(rows)
    if args.limit:
        train, val, test, gold = train[:args.limit], val[:args.limit // 4], test[:args.limit // 4], gold[:args.limit // 2]
    say(f"huấn luyện {len(train)} | validation {len(val)} | test {len(test)} | vàng {len(gold)} | nhãn {label_counts(train)}")

    scorer = Scorer(None, args.threads)             # nạp PhoBERT gốc, đầu phân loại khởi tạo ngẫu nhiên
    model, tok = scorer.model, scorer.tokenizer
    say("đang tách từ toàn bộ văn bản huấn luyện...")
    for r in train + val + test + gold:
        segment(r["text"])
    y_train = np.array([r["y"] for r in train])
    counts = np.bincount(y_train, minlength=3)
    weights = torch.tensor(len(y_train) / (3 * np.maximum(counts, 1)), dtype=torch.float32)   # cân bằng lớp (trung tính ít hơn)
    loss_fn = torch.nn.CrossEntropyLoss(weight=weights)

    no_decay = ("bias", "LayerNorm.weight")
    params = [
        {"params": [p for n, p in model.named_parameters() if not any(x in n for x in no_decay)], "weight_decay": 0.01},
        {"params": [p for n, p in model.named_parameters() if any(x in n for x in no_decay)], "weight_decay": 0.0},
    ]
    optimizer = torch.optim.AdamW(params, lr=args.lr)
    lengths = [len(r["text"].split()) for r in train]
    steps_per_epoch = len(length_buckets(lengths, args.batch_size))
    total = steps_per_epoch * args.epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, int(0.1 * total), total)
    say(f"{steps_per_epoch} bước mỗi epoch, tổng {total}, lớp trọng số {weights.numpy().round(2).tolist()}")

    best_f1, best_epoch, history = -1.0, 0, []
    started = time.time()
    for epoch in range(1, args.epochs + 1):
        model.train()
        running, seen = 0.0, 0
        for step, idx in enumerate(length_buckets(lengths, args.batch_size, SEED + epoch), 1):
            enc = scorer.encode([train[i]["text"] for i in idx])
            labels = torch.tensor([train[i]["y"] for i in idx])
            loss = loss_fn(model(**enc).logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step(); scheduler.step(); optimizer.zero_grad()
            running += loss.item() * len(idx); seen += len(idx)
            if step % 10 == 0 or step == steps_per_epoch:
                say(f"epoch {epoch}/{args.epochs} bước {step}/{steps_per_epoch} loss {running / seen:.4f} "
                    f"({(time.time() - started) / 60:.1f} phút)")
        model.eval()
        proba = scorer.predict_proba([r["text"] for r in val])
        m = metrics([r["y"] for r in val], proba.argmax(1).tolist())
        history.append({"epoch": epoch, "train_loss": round(running / seen, 4), "val_macro_f1": m["macro_f1"]})
        say(f"== epoch {epoch}: loss {running / seen:.4f} | validation macro-F1 {m['macro_f1']} accuracy {m['accuracy']}")
        if m["macro_f1"] > best_f1:
            best_f1, best_epoch = m["macro_f1"], epoch
            save_model(model, tok, args.out_dir, {
                "model": "M1_phobert", "base": BASE_MODEL, "labels": LABELS, "max_len": MAX_LEN,
                "trained_on": date.today().isoformat(), "best_epoch": epoch, "val_macro_f1": best_f1,
                "train_size": len(train), "label_source": "LLM (claude-sonnet-5-5) theo RUBRIC, không phải nhãn người"})
            say(f"   đã lưu epoch tốt nhất ({best_f1})")

    say(f"chọn epoch {best_epoch}; nạp lại để đo test và tập vàng (một lần)")
    best = Scorer(args.out_dir, args.threads)
    result = {"model": "phobert", "base": BASE_MODEL, "epochs": args.epochs, "lr": args.lr, "batch_size": args.batch_size,
              "best_epoch": best_epoch, "validation_macro_f1": best_f1, "history": history,
              "train_minutes": round((time.time() - started) / 60, 1)}
    for name, rows_ in (("test", test), ("gold_llm", gold)):
        proba = best.predict_proba([r["text"] for r in rows_])
        result[name] = metrics([r["y"] for r in rows_], proba.argmax(1).tolist())
        say(f"{name.upper():8} macro-F1 = {result[name]['macro_f1']} accuracy = {result[name]['accuracy']} "
            f"F1/lớp = {result[name]['f1_per_class']}")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    say("đã ghi", args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
