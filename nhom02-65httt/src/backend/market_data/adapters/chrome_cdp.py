from __future__ import annotations
import asyncio
import json
import os
from urllib.parse import urlparse

class ChromeCdpCollector:
    """Optional passive network-response collector for an operator-owned Chrome session.

    Requires `pip install playwright` and Chrome started with remote debugging enabled.
    It does not log in, bypass access controls, click purchase actions, or alter listings.
    """
    def __init__(self, cdp_url: str = "http://127.0.0.1:9222", ingest_url: str | None = None):
        self.cdp_url = cdp_url
        self.ingest_url = ingest_url or os.getenv("CRAWLER_CDP_INGEST_URL")

    async def collect(self, duration_seconds: int = 60):
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError("Cần cài playwright và chạy `playwright install chromium`") from exc
        captured = []
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(self.cdp_url)
            contexts = browser.contexts
            if not contexts:
                raise RuntimeError("Chrome CDP không có context đang mở")
            for context in contexts:
                for page in context.pages:
                    async def on_response(response):
                        host = (urlparse(response.url).hostname or "").lower()
                        if not any(x in host for x in ("shopee", "lazada", "tiktok")):
                            return
                        ctype = response.headers.get("content-type", "")
                        if "json" not in ctype.lower(): return
                        try:
                            payload = await response.json()
                            captured.append({"url": response.url, "status": response.status, "payload": payload})
                        except Exception:
                            return
                    page.on("response", on_response)
            await asyncio.sleep(max(1, int(duration_seconds)))
            await browser.close()
        if self.ingest_url and captured:
            import requests
            r = requests.post(self.ingest_url, json={"items": captured}, timeout=20)
            r.raise_for_status()
        return {"captured": len(captured), "ingested": bool(self.ingest_url), "items": captured}

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--cdp", default="http://127.0.0.1:9222")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(ChromeCdpCollector(args.cdp).collect(args.duration)), ensure_ascii=False, default=str))

if __name__ == "__main__": main()
