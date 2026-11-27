from __future__ import annotations
import pandas as pd
from .base import CompetitorSourceAdapter

class TikiOpenApiAdapter(CompetitorSourceAdapter):
    marketplace = "TIKI"
    BASE_URL = "https://tiki.vn/api/v2/products"

    def fetch(self, keyword: str, limit: int = 20, **kwargs) -> pd.DataFrame:
        payload = self.request(self.BASE_URL, params={"q": keyword, "limit": min(max(int(limit), 1), 100)}).json()
        products = payload.get("data", []) if isinstance(payload, dict) else []
        rows = []
        for p in products:
            if not isinstance(p, dict) or not p.get("id") or not p.get("price"):
                continue
            price = float(p["price"])
            rows.append(self.record(
                marketplace="TIKI", category=keyword, product_id=str(p["id"]),
                title=p.get("name", ""), seller=(p.get("seller", {}) or {}).get("name", "") if isinstance(p.get("seller"), dict) else "",
                brand=(p.get("brand", {}) or {}).get("name", "") if isinstance(p.get("brand"), dict) else str(p.get("brand", "")),
                price_vnd=price, original_price_vnd=p.get("list_price"),
                discount_percent=p.get("discount_rate"), rating=p.get("rating_average"),
                review_count=p.get("review_count"), sold=p.get("quantity_sold"),
                url=p.get("url_path", ""), confidence=0.85,
            ))
        return pd.DataFrame(rows)
