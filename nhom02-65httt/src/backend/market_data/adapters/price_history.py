from __future__ import annotations
import os
import pandas as pd
from .base import CompetitorSourceAdapter

class PriceHistoryApiAdapter(CompetitorSourceAdapter):
    """Configurable JSON endpoint adapter; requires a permitted, verified endpoint.

    Set PRICE_HISTORY_API_URL to the endpoint and pass product identifiers as params.
    Response parser accepts a list or common `data`/`products` list containers.
    """
    marketplace = "PRICE_HISTORY_API"

    def fetch(self, product_id: str, **kwargs) -> pd.DataFrame:
        endpoint = os.getenv("PRICE_HISTORY_API_URL")
        if not endpoint:
            raise RuntimeError("Chưa cấu hình PRICE_HISTORY_API_URL; cần xác minh endpoint và quyền truy cập trước khi crawl.")
        payload = self.request(endpoint, params={"product_id": product_id}).json()
        items = payload if isinstance(payload, list) else next((payload.get(k) for k in ("data", "products", "history") if isinstance(payload, dict) and isinstance(payload.get(k), list)), [])
        rows = []
        for item in items:
            if not isinstance(item, dict): continue
            price = item.get("price_vnd", item.get("price"))
            observed = item.get("observed_at", item.get("date", item.get("timestamp")))
            if price is None or observed is None: continue
            rows.append(self.record(
                marketplace=str(item.get("marketplace", self.marketplace)).upper(),
                category=item.get("category", ""), product_id=str(item.get("product_id", product_id)),
                title=item.get("title", item.get("name", "")), brand=item.get("brand", ""),
                price_vnd=float(price), original_price_vnd=item.get("original_price_vnd"),
                observed_at=observed, url=item.get("url", ""), confidence=0.6,
            ))
        return pd.DataFrame(rows)
