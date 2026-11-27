from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from .normalize import load_dataset
from .matching import match_catalog

def main():
    parser = argparse.ArgumentParser(description="Member 3 market data tools")
    sub = parser.add_subparsers(dest="command", required=True)
    norm = sub.add_parser("normalize", help="Validate and normalize competitor CSV")
    norm.add_argument("--input", default="../../datasets/competitor-prices-vnd.csv")
    norm.add_argument("--output", default="data/competitor_prices_normalized.csv")
    norm = sub.add_parser("match", help="Match ERP products CSV against competitor dataset")
    norm.add_argument("--erp", required=True, help="CSV columns: sku,name,brand")
    norm.add_argument("--competitors", default="../../datasets/competitor-prices-vnd.csv")
    norm.add_argument("--output", default="data/sku_match_candidates.csv")
    args = parser.parse_args()
    if args.command == "normalize":
        df = load_dataset(args.input); output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True); df.to_csv(output, index=False)
        print(json.dumps({"rows_valid": len(df), "marketplaces": df.marketplace.value_counts().to_dict(),
            "categories": int(df.category.nunique()), "observed_at_unique": int(df.observed_at.nunique()),
            "price_min_vnd": float(df.price_vnd.min()), "price_max_vnd": float(df.price_vnd.max()),
            "possible_outliers_below_1000": int((df.price_vnd < 1000).sum()),
            "possible_outliers_above_500m": int((df.price_vnd > 500_000_000).sum()), "output": str(output)}, ensure_ascii=False, indent=2))
    else:
        erp = pd.read_csv(args.erp).fillna("").to_dict(orient="records")
        competitors = load_dataset(args.competitors)
        result = match_catalog(erp, competitors, top_n=5)
        output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True); result.to_csv(output, index=False)
        print(json.dumps({"erp_products": len(erp), "candidates": len(result), "status_counts": result.status.value_counts().to_dict(), "output": str(output)}, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
