from __future__ import annotations
import json
from urllib.parse import urlparse
import pandas as pd
from bs4 import BeautifulSoup
from .base import CompetitorSourceAdapter

ALLOWED_RETAIL_DOMAINS = {"websosanh.vn", "www.websosanh.vn", "cellphones.com.vn", "www.cellphones.com.vn", "memoryzone.com.vn", "www.memoryzone.com.vn"}

class RetailHtmlAdapter(CompetitorSourceAdapter):
    marketplace = "RETAIL_WEB"

    def fetch(self, url: str, **kwargs) -> pd.DataFrame:
        host = (urlparse(url).hostname or "").lower()
        if host not in ALLOWED_RETAIL_DOMAINS:
            raise ValueError(f"Domain chưa được cho phép: {host}")
        html = self.request(url).text
        soup = BeautifulSoup(html, "html.parser")
        rows = []
        for node in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                data = json.loads(node.string or node.get_text())
            except (json.JSONDecodeError, TypeError):
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and "@graph" in item:
                    items.extend(x for x in item["@graph"] if isinstance(x, dict))
                if not isinstance(item, dict):
                    continue
                typ = item.get("@type", [])
                if "Product" not in (typ if isinstance(typ, list) else [typ]):
                    continue
                offers = item.get("offers", {})
                if isinstance(offers, list): offers = offers[0] if offers else {}
                if isinstance(offers, dict) and offers.get("price"):
                    rows.append(self.record(
                        marketplace="RETAIL_WEB", category="retail", product_id=str(item.get("sku") or item.get("mpn") or item.get("url") or url),
                        title=item.get("name", ""), brand=(item.get("brand", {}) or {}).get("name", "") if isinstance(item.get("brand"), dict) else item.get("brand", ""),
                        price_vnd=float(offers["price"]), original_price_vnd=None,
                        rating=(item.get("aggregateRating", {}) or {}).get("ratingValue") if isinstance(item.get("aggregateRating"), dict) else None,
                        review_count=(item.get("aggregateRating", {}) or {}).get("reviewCount") if isinstance(item.get("aggregateRating"), dict) else None,
                        url=item.get("url", url), confidence=0.65,
                    ))
        return pd.DataFrame(rows)
