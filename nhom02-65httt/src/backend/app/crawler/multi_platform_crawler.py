"""
Multi-Platform E-Commerce & Price-History Crawler (Mode A & Mode B)
===================================================================
Hỗ trợ chạy ngay không cần đăng nhập:
  - Lazada Direct PDP (bóc tách pdpTrackingData, JSON-LD, __moduleData__)
  - Shopee Keyword Discovery + Lịch sử giá 32-56+ điểm (lichsugia.com + lichsugia.net)
  - Tiki Open API v2 (/api/v2/products)
  - Đối chiếu đa sàn qua giarevn.com & apiv3.beecost.vn (muathongminh.vn)
  - Giá tham chiếu bán lẻ chính hãng (cellphones.com.vn, websosanh.vn)

Chạy lệnh từ thư mục `src/backend/`:
    python -m app.crawler.multi_platform_crawler
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import time
from datetime import UTC, datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
OUT_FILE = os.path.join(
    os.path.dirname(__file__), "samples", "verified_crawl_output.json"
)


def make_client() -> httpx.Client:
    return httpx.Client(
        timeout=15.0,
        follow_redirects=True,
        verify=False,
        headers={
            "User-Agent": UA,
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )


def _parse_vnd(price_str: Any) -> int | None:
    if price_str is None:
        return None
    if isinstance(price_str, int | float):
        return int(price_str)
    digits = re.sub(r"[^\d]", "", str(price_str))
    return int(digits) if digits else None


def crawl_lazada_direct_pdp(client: httpx.Client, url: str) -> dict[str, Any]:
    """Mode A: Crawl trực tiếp trang chi tiết sản phẩm Lazada (HTTP 200, không cần login)."""
    t0 = time.time()
    r = client.get(url, headers={"Accept": "text/html"})
    latency_ms = int((time.time() - t0) * 1000)
    html = r.text

    result: dict[str, Any] = {
        "source": "lazada.vn (Direct PDP)",
        "url": str(r.url),
        "http_status": r.status_code,
        "latency_ms": latency_ms,
        "html_bytes": len(html.encode("utf-8", errors="ignore")),
    }

    # 1. Bóc tách pdpTrackingData (chứa giá bán thực tế, SKU, brand)
    m_track = re.search(r'pdpTrackingData\s*=\s*"((?:\\.|[^"\\])*)";', html, re.S)
    if m_track:
        try:
            decoded_json_str = json.loads(f'"{m_track.group(1)}"')
            track = json.loads(decoded_json_str)
            result["name"] = track.get("pdt_name")
            result["price_raw"] = track.get("pdt_price")
            result["price_vnd"] = _parse_vnd(track.get("pdt_price"))
            result["brand"] = track.get("brand_name")
            result["item_id"] = track.get("pdt_sku")
            result["sku_id"] = track.get("pdt_simplesku")
        except Exception as exc:
            result["tracking_parse_error"] = str(exc)

    # 2. Bóc tách JSON-LD Product (tình trạng InStock, danh mục)
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            ld = json.loads(tag.string or "{}")
            if isinstance(ld, dict) and ld.get("@type") == "Product":
                result["name"] = result.get("name") or ld.get("name")
                result["category"] = ld.get("category")
                offers = ld.get("offers") or {}
                if isinstance(offers, dict):
                    result["availability"] = offers.get("availability")
                break
        except Exception:
            continue

    # 3. Bóc tách __moduleData__ (sellerId, shop info)
    m_mod = re.search(r"__moduleData__\s*=\s*(\{.*?\});\s*\n", html, re.S)
    if m_mod:
        try:
            md = json.loads(m_mod.group(1))
            pk = md.get("data", {}).get("root", {}).get("fields", {}).get("primaryKey", {})
            result["seller_id"] = pk.get("sellerId")
        except Exception:
            pass

    return result


def crawl_shopee_via_keyword_and_history(
    client: httpx.Client, keyword: str, max_items: int = 3
) -> list[dict[str, Any]]:
    """
    Mode B: Tìm sản phẩm Shopee theo từ khóa qua lichsugia.com/api/similar-products.php,
    sau đó lấy chi tiết & lịch sử giá từ lichsugia.net + lichsugia.com/api/price-history.php.
    """
    r_sim = client.post(
        "https://lichsugia.com/api/similar-products.php",
        data={"title": keyword, "itemid": "1"},
        headers={
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://lichsugia.com/",
        },
    )
    matches = re.findall(r'href="/s/shopee-(\d+)\.(\d+)"', r_sim.text)
    seen: set[tuple[str, str]] = set()
    unique_pairs: list[tuple[str, str]] = []
    for sid, iid in matches:
        if (sid, iid) not in seen:
            seen.add((sid, iid))
            unique_pairs.append((sid, iid))

    results: list[dict[str, Any]] = []
    for shop_id, item_id in unique_pairs[:max_items]:
        t0 = time.time()
        r_net = client.get(
            f"https://lichsugia.net/backend-api/api/public/products/platform/{shop_id}/{item_id}"
        )
        latency_ms = int((time.time() - t0) * 1000)
        if r_net.status_code != 200:
            continue
        d = r_net.json()

        # Lấy thống kê 90 ngày + cảnh báo sale ảo từ lichsugia.com
        r_com = client.post(
            "https://lichsugia.com/api/price-history.php",
            data={
                "_saToken": "",
                "tp": "history",
                "history_action": "list_chart",
                "filter[days]": "90",
                "filter[domain]": "shopee",
                "filter[sp_id]": f"{shop_id}.{item_id}",
                "filter[title]": d.get("name", ""),
                "filter[price]": str(d.get("price", 0)),
                "filter[original_price]": str(d.get("price_before_discount", 0)),
                "filter[image]": d.get("image", ""),
            },
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://lichsugia.com/",
            },
        )
        com_statis = {}
        if r_com.status_code == 200:
            with contextlib.suppress(Exception):
                com_statis = r_com.json().get("statis", {})

        history = d.get("price_history") or []
        results.append(
            {
                "source": "shopee (via lichsugia.net + lichsugia.com)",
                "query_keyword": keyword,
                "shop_id": shop_id,
                "item_id": item_id,
                "product_url": d.get("product_link"),
                "name": d.get("name"),
                "is_mall_shop": d.get("is_mall_shop"),
                "price_vnd": d.get("price"),
                "original_price_vnd": d.get("price_before_discount"),
                "price_min_vnd": d.get("price_min"),
                "price_max_vnd": d.get("price_max"),
                "sold": d.get("sold"),
                "rating_avg": round(float(d.get("rating_avg") or 0), 2),
                "history_points_count": len(history),
                "history_sample_first_3": history[:3],
                "history_sample_last_3": history[-3:],
                "statis_90d": com_statis,
                "latency_ms": latency_ms,
            }
        )
        time.sleep(0.4)
    return results


def crawl_tiki_open_api(
    client: httpx.Client, keyword: str, limit: int = 3
) -> list[dict[str, Any]]:
    """Mode A: Truy vấn Public API v2 của Tiki."""
    t0 = time.time()
    r = client.get(
        "https://tiki.vn/api/v2/products",
        params={"limit": limit, "q": keyword},
        headers={"Accept": "application/json"},
    )
    latency_ms = int((time.time() - t0) * 1000)
    items = r.json().get("data", []) if r.status_code == 200 else []
    out = []
    for p in items[:limit]:
        out.append(
            {
                "source": "tiki.vn (Public API v2)",
                "query_keyword": keyword,
                "id": p.get("id"),
                "sku": p.get("sku"),
                "name": p.get("name"),
                "brand": p.get("brand_name"),
                "price_vnd": p.get("price"),
                "original_price_vnd": p.get("original_price"),
                "discount_rate": p.get("discount_rate"),
                "sold": (p.get("quantity_sold") or {}).get("value"),
                "rating_avg": p.get("rating_average"),
                "latency_ms": latency_ms,
            }
        )
    return out


def crawl_giarevn_by_url(client: httpx.Client, product_url: str) -> dict[str, Any]:
    """Mode B: Tra cứu sản phẩm và biểu đồ giá trên giarevn.com (Astro Server Island)."""
    t0 = time.time()
    r = client.post(
        "https://giarevn.com/_actions/searchProductByUrl",
        json=product_url,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://giarevn.com",
            "Referer": "https://giarevn.com/",
        },
    )
    res: dict[str, Any] = {
        "source": "giarevn.com",
        "target_url": product_url,
        "http_status": r.status_code,
        "latency_ms": int((time.time() - t0) * 1000),
    }
    if r.status_code != 200:
        return res
    try:
        arr = r.json()
        slug = next((x for x in arr if isinstance(x, str) and x.startswith("/product/")), None)
        res["slug"] = slug
        if slug:
            html_p = client.get(f"https://giarevn.com{slug}").text
            m_isl = re.search(r'/_server-islands/PriceHistoryChart\?[^"\'\s>]+', html_p)
            if m_isl:
                chart_html = client.get(f"https://giarevn.com{m_isl.group(0)}").text
                soup = BeautifulSoup(chart_html, "html.parser")
                canvas = soup.find("canvas", id="priceChart")
                if canvas:
                    res["prices"] = json.loads(canvas.get("data-prices", "[]"))
                    res["labels"] = json.loads(canvas.get("data-labels", "[]"))
    except Exception as exc:
        res["parse_error"] = str(exc)
    return res


def crawl_retail_benchmarks(client: httpx.Client) -> dict[str, Any]:
    """Mode A: Lấy giá bán lẻ chính hãng (CellphoneS) và cổng so sánh giá (Websosanh)."""
    benchmarks: dict[str, Any] = {}

    # 1. CellphoneS chuột máy tính
    r_cps = client.get(
        "https://cellphones.com.vn/phu-kien/chuot-ban-phim-may-tinh/chuot.html"
    )
    soup_cps = BeautifulSoup(r_cps.text, "html.parser")
    cps_items = []
    for info in soup_cps.select(".product-info-container, .product-item"):
        title_el = info.select_one("h3")
        price_el = info.select_one(".product__price--show")
        if title_el and price_el:
            cps_items.append(
                {
                    "name": title_el.get_text(strip=True),
                    "price_vnd": _parse_vnd(price_el.get_text(strip=True)),
                }
            )
    benchmarks["cellphones.com.vn"] = {
        "http_status": r_cps.status_code,
        "items_count": len(cps_items),
        "sample": cps_items[:5],
    }

    # 2. Websosanh.vn
    r_wss = client.get("https://websosanh.vn/s/chuot+logitech+m185.htm")
    prices_wss = re.findall(r"[0-9]{1,3}(?:[.,][0-9]{3})+\s*[₫đ]", r_wss.text)
    benchmarks["websosanh.vn"] = {
        "http_status": r_wss.status_code,
        "prices_extracted_count": len(prices_wss),
        "sample_prices": prices_wss[:8],
    }
    return benchmarks


def main() -> None:
    print("=== Bắt đầu chạy Multi-Platform Crawler (Mode A & B) ===")
    with make_client() as client:
        lazada_urls = [
            "https://www.lazada.vn/products/chuot-khong-day-logitech-m185-wireless-usbxam-den-hang-chinh-hang-i2174655511.html",
            "https://www.lazada.vn/products/chuot-khong-day-logitech-m331-den-i683118869.html",
            "https://www.lazada.vn/products/ban-phim-gaming-logitech-g213-prodigy-rgb-i1249690979.html",
        ]
        lazada_data = [crawl_lazada_direct_pdp(client, u) for u in lazada_urls]
        print(f"[OK] Lazada Direct PDP: {len(lazada_data)} SKU")
        for it in lazada_data:
            print(
                f"   - {it.get('name')} -> {it.get('price_vnd')} VND "
                f"(HTTP {it.get('http_status')}, {it.get('latency_ms')}ms)"
            )

        shopee_data = crawl_shopee_via_keyword_and_history(
            client, "Chuột không dây Logitech M185", max_items=3
        )
        print(f"[OK] Shopee (via LichSuGia Keyword + History): {len(shopee_data)} SKU")
        for it in shopee_data:
            print(
                f"   - {str(it.get('name'))[:55]} -> {it.get('price_vnd')} VND "
                f"(sold={it.get('sold')}, history_pts={it.get('history_points_count')})"
            )

        tiki_data = crawl_tiki_open_api(client, "chuot logitech m185", limit=3)
        print(f"[OK] Tiki Open API v2: {len(tiki_data)} SKU")
        for it in tiki_data:
            print(
                f"   - {str(it.get('name'))[:55]} -> {it.get('price_vnd')} VND "
                f"(sold={it.get('sold')})"
            )

        giarevn_sample = crawl_giarevn_by_url(
            client, "https://shopee.vn/product/52679373/1592328943"
        )
        print(
            f"[OK] GiaReVN Chart Island: status={giarevn_sample.get('http_status')}, "
            f"points={len(giarevn_sample.get('prices', []))}"
        )

        retail_data = crawl_retail_benchmarks(client)
        print(
            "[OK] Retail Benchmarks: "
            f"CellphoneS={retail_data['cellphones.com.vn']['items_count']} items, "
            f"Websosanh={retail_data['websosanh.vn']['prices_extracted_count']} prices"
        )

    payload = {
        "crawled_at_utc": datetime.now(UTC).isoformat(),
        "lazada_direct_pdp": lazada_data,
        "shopee_via_history_apis": shopee_data,
        "tiki_open_api": tiki_data,
        "giarevn_chart_sample": giarevn_sample,
        "retail_benchmarks": retail_data,
    }
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\nĐã lưu dữ liệu crawl thật tại: {OUT_FILE}")


if __name__ == "__main__":
    main()
