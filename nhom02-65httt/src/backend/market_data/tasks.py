from __future__ import annotations
import os
from pathlib import Path
from .celery_app import celery_app
from .normalize import load_dataset

@celery_app.task(name="market_data.tasks.validate_dataset_task")
def validate_dataset_task():
    default = Path(__file__).resolve().parents[3] / "datasets" / "competitor-prices-vnd.csv"
    csv_path = Path(os.getenv("COMPETITOR_DATASET_PATH", str(default)))
    if not csv_path.exists():
        return {"status": "CONFIG_REQUIRED", "message": f"Dataset not found: {csv_path}"}
    df = load_dataset(str(csv_path))
    return {"status": "OK", "rows_valid": int(len(df)),
            "marketplaces": sorted(df["marketplace"].unique().tolist()),
            "observed_at_unique": int(df["observed_at"].nunique())}

@celery_app.task(name="market_data.tasks.normalize_snapshot_task")
def normalize_snapshot_task(input_path: str | None = None, output_path: str | None = None):
    default = Path(__file__).resolve().parents[3] / "datasets" / "competitor-prices-vnd.csv"
    source = Path(input_path or os.getenv("COMPETITOR_DATASET_PATH", str(default)))
    if not source.exists():
        return {"status": "CONFIG_REQUIRED", "message": f"Dataset not found: {source}"}
    df = load_dataset(source)
    target = Path(output_path or os.getenv("NORMALIZED_DATASET_PATH", "data/competitor_prices_normalized.csv"))
    target.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target, index=False)
    return {"status": "OK", "rows": len(df), "output": str(target)}
