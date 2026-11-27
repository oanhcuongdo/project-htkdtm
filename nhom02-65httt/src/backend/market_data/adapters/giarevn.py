from __future__ import annotations
import json
import re
import pandas as pd
from bs4 import BeautifulSoup
from .base import CompetitorSourceAdapter

class GiarevnAstroAdapter(CompetitorSourceAdapter):
    """Proof-of-concept parser for Giarevn product price-history pages.

    Endpoint/page payloads can change; validate response structure and site terms
    before enabling scheduled collection in a shared environment.
    """
    marketplace = "GIAREVN"
    SEARCH_ACTION = "https://giarevn.com/_actions/searchProductByUrl"

    def fetch(self, product_url: str, **kwargs) -> pd.DataFrame:
        response = self.session.post(self.SEARCH_ACTION, data={"url": product_url}, timeout=self.timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # The chart payload is sometimes embedded as data attributes on a canvas.
        canvas = soup.find("canvas", id="priceChart")
        if canvas is None:
            # Some Astro responses return a fragment containing a base64/string JSON payload.
            match = re.search(r'"data-prices"\s*:\s*(\[[^]]+\])', response.text)
            prices = json.loads(match.group(1)) if match else []
            labels_match = re.search(r'"data-labels"\s*:\s*(\[[^]]+\])', response.text)
            labels = json.loads(labels_match.group(1)) if labels_match else []
        else:
            prices = json.loads(canvas.get("data-prices", "[]"))
            labels = json.loads(canvas.get("data-labels", "[]"))
        rows = []
        for i, price in enumerate(prices):
            if price is None: continue
            rows.append(self.record(marketplace="GIAREVN", category="price_history",
                product_id=product_url, title=product_url, price_vnd=float(price),
                observed_at=labels[i] if i < len(labels) else None,
                url=product_url, confidence=0.55))
        return pd.DataFrame(rows)
