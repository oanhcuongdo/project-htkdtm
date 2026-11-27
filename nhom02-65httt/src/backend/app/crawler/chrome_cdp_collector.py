"""
Mode C (v2.0): Browser-in-the-Loop Chrome CDP Collector (Shopee / Lazada / TikTok Shop)
======================================================================================
Kế thừa & nâng cấp kiến trúc từ `erqyan/ShopeeScrapping` (browser_crawl.mjs) và
`dtungpka/shopee-scraper`:
  1. Tự động phát hiện & khởi chạy Chrome thật trên cổng Debug 9222 với Persistent
     Profile (`%LOCALAPPDATA%\\ERP_SmartPricing_ChromeProfile`).
  2. Hỗ trợ 3 chế độ CLI:
     - `--diagnose` : Kiểm tra sức khỏe phiên CDP, tài khoản đăng nhập Shopee, trạng thái
       SDK ký số (`window.fetch`) và độ lệch giờ hệ thống.
     - `--url U1 U2`: Mở tuần tự danh sách URL Shopee/Lazada/TikTok Shop, đợi thông minh
       (dừng sớm ngay khi bắt được JSON), trích xuất & chuẩn hóa thành bản ghi ERP.
     - `--listen 60`: Chế độ Live Passive Sniffer — lắng nghe thụ động trên tất cả tab
       Chrome đang mở trong 60 giây khi người dùng tự lướt/tìm kiếm trên sàn.
  3. An toàn & minh bạch: Nếu gặp màn hình xác minh/đăng nhập (`/verify/`,
     `Security Check`, `punish`), script ghi nhận trạng thái và dừng thu thập URL đó để
     người vận hành tự xử lý trực tiếp trên cửa sổ Chrome thật.
"""

from __future__ import annotations

import argparse
import email.utils
import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any

from playwright.sync_api import BrowserContext, Page, Response, sync_playwright

OUT_FILE = os.path.join(os.path.dirname(__file__), "cdp_captured_payloads.json")
DEFAULT_PROFILE_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "ERP_SmartPricing_ChromeProfile",
)


def find_browser_executable() -> str | None:
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def is_cdp_up(cdp_url: str) -> dict[str, Any] | None:
    try:
        req = urllib.request.Request(f"{cdp_url.rstrip('/')}/json/version")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception:
        return None
    return None


def ensure_chrome_cdp_running(
    cdp_url: str, profile_dir: str = DEFAULT_PROFILE_DIR, auto_launch: bool = True
) -> dict[str, Any]:
    info = is_cdp_up(cdp_url)
    if info:
        return {"launched": False, "already_running": True, "version_info": info}
    if not auto_launch:
        raise RuntimeError(f"CDP chưa hoạt động tại {cdp_url} (và --no-launch đang bật).")

    exe = find_browser_executable()
    if not exe:
        raise RuntimeError("Không tìm thấy Google Chrome hoặc Microsoft Edge trên máy.")

    parsed = urllib.parse.urlparse(cdp_url)
    port = parsed.port or 9222
    os.makedirs(profile_dir, exist_ok=True)

    cmd = [
        exe,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--start-maximized",
        "--new-window",
        "--no-first-run",
        "--no-default-browser-check",
        "--remote-allow-origins=*",
        "https://lichsugia.net/",
    ]
    if os.name == "nt":
        # Dùng cmd start để Windows hiển thị cửa sổ Chrome bình thường lên Foreground
        arg_str = " ".join(f'"{c}"' if " " in c else c for c in cmd)
        subprocess.Popen(
            f'start "" {arg_str}',
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    deadline = time.time() + 15.0
    while time.time() < deadline:
        info = is_cdp_up(cdp_url)
        if info:
            return {
                "launched": True,
                "already_running": False,
                "executable": exe,
                "profile_dir": profile_dir,
                "version_info": info,
            }
        time.sleep(0.5)

    raise RuntimeError(
        f"Đã khởi chạy {exe} ở cổng {port} nhưng chưa kết nối được CDP. "
        "Hãy đóng các cửa sổ Chrome cùng profile cũ nếu có rồi thử lại."
    )


def _shopee_vnd(val: Any) -> int | None:
    if isinstance(val, (int, float)) and val > 0:
        return int(round(val / 100000.0)) if val >= 100000 else int(val)
    return None


def _parse_vnd_str(val: Any) -> int | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    digits = re.sub(r"[^\d]", "", str(val))
    return int(digits) if digits else None


def parse_shopee_pdp(body: dict[str, Any], api_url: str) -> dict[str, Any] | None:
    data = body.get("data") or {}
    item = data.get("item") or data.get("item_data") or {}
    if not item:
        return None
    review = data.get("product_review") or {}
    shop = data.get("shop_detailed") or {}

    models_out = []
    for m in (item.get("models") or [])[:15]:
        models_out.append(
            {
                "model_id": m.get("modelid") or m.get("model_id"),
                "name": m.get("name"),
                "price_vnd": _shopee_vnd(m.get("price")),
                "price_before_discount_vnd": _shopee_vnd(m.get("price_before_discount")),
                "stock": m.get("stock"),
            }
        )

    return {
        "platform": "shopee",
        "record_type": "pdp",
        "api_url": api_url,
        "shop_id": item.get("shopid") or item.get("shop_id"),
        "item_id": item.get("itemid") or item.get("item_id"),
        "name": item.get("title") or item.get("name"),
        "price_vnd": _shopee_vnd(item.get("price") or item.get("price_min")),
        "price_max_vnd": _shopee_vnd(item.get("price_max")),
        "original_price_vnd": _shopee_vnd(
            item.get("price_before_discount") or item.get("price_max_before_discount")
        ),
        "stock": item.get("stock"),
        "sold": review.get("historical_sold") or item.get("historical_sold") or item.get("sold"),
        "rating_star": review.get("rating_star") or (item.get("item_rating") or {}).get("rating_star"),
        "rating_count": review.get("rating_count"),
        "shop_name": shop.get("name") or (shop.get("account") or {}).get("username"),
        "is_official_shop": shop.get("is_official_shop") or item.get("is_official_shop"),
        "models": models_out,
    }


def parse_shopee_search(body: dict[str, Any], api_url: str) -> dict[str, Any] | None:
    items = body.get("items") or []
    if not items:
        return None
    parsed_items = []
    for entry in items[:20]:
        ib = entry.get("item_basic") or entry
        if not ib.get("itemid"):
            continue
        parsed_items.append(
            {
                "shop_id": ib.get("shopid"),
                "item_id": ib.get("itemid"),
                "name": ib.get("name"),
                "price_vnd": _shopee_vnd(ib.get("price") or ib.get("price_min")),
                "original_price_vnd": _shopee_vnd(ib.get("price_before_discount")),
                "historical_sold": ib.get("historical_sold"),
                "stock": ib.get("stock"),
                "is_official_shop": ib.get("is_official_shop"),
                "shop_location": ib.get("shop_location"),
            }
        )
    return {
        "platform": "shopee",
        "record_type": "search_list",
        "api_url": api_url,
        "items_count": len(parsed_items),
        "items": parsed_items,
    }


def parse_lazada_from_dom(html: str, page_url: str) -> dict[str, Any] | None:
    out: dict[str, Any] = {"platform": "lazada", "record_type": "pdp_dom", "url": page_url}
    m_track = re.search(r'pdpTrackingData\s*=\s*"((?:\\.|[^"\\])*)";', html, re.S)
    if m_track:
        try:
            track = json.loads(json.loads(f'"{m_track.group(1)}"'))
            out["name"] = track.get("pdt_name")
            out["price_vnd"] = _parse_vnd_str(track.get("pdt_price"))
            out["brand"] = track.get("brand_name")
            out["item_id"] = track.get("pdt_sku")
            out["sku_id"] = track.get("pdt_simplesku")
        except Exception:
            pass
    m_mod = re.search(r"__moduleData__\s*=\s*(\{.*?\});\s*\n", html, re.S)
    if m_mod:
        try:
            md = json.loads(m_mod.group(1))
            fields = md.get("data", {}).get("root", {}).get("fields", {})
            pk = fields.get("primaryKey", {})
            out["seller_id"] = pk.get("sellerId")
            seller = fields.get("seller") or {}
            if seller.get("name"):
                out["shop_name"] = seller.get("name")
        except Exception:
            pass
    return out if (out.get("name") or out.get("price_vnd")) else None


def parse_tiktok_from_dom(html: str, page_url: str) -> dict[str, Any] | None:
    for script_id in ("__UNIVERSAL_DATA_FOR_REHYDRATION__", "SIGI_STATE"):
        m = re.search(
            rf'<script[^>]*id="{script_id}"[^>]*>(.*?)</script>', html, re.S
        )
        if m:
            try:
                data = json.loads(m.group(1))
                return {
                    "platform": "tiktok_shop",
                    "record_type": f"ssr_{script_id.lower()}",
                    "url": page_url,
                    "top_keys": list(data.keys())[:10] if isinstance(data, dict) else [],
                    "payload_bytes": len(m.group(1)),
                }
            except Exception:
                pass
    return None


def is_interesting_api(url: str) -> bool:
    patterns = (
        "/api/v4/pdp/get_pc",
        "/api/v4/item/get",
        "/api/v4/search/search_items",
        "/api/v2/item/get_ratings",
        "mtop.lazada.",
        "/api/v1/shop/",
        "product_info",
    )
    return any(p in url for p in patterns)


def classify_captured_response(api_url: str, body: dict[str, Any]) -> dict[str, Any]:
    if "/api/v4/pdp/get_pc" in api_url or "/api/v4/item/get" in api_url:
        parsed = parse_shopee_pdp(body, api_url)
        if parsed:
            return parsed
    if "/api/v4/search/search_items" in api_url:
        parsed = parse_shopee_search(body, api_url)
        if parsed:
            return parsed
    if "mtop.lazada." in api_url:
        return {
            "platform": "lazada",
            "record_type": "mtop_xhr",
            "api_url": api_url,
            "data_keys": list((body.get("data") or {}).keys())[:15]
            if isinstance(body.get("data"), dict)
            else [],
        }
    return {
        "platform": "unknown_or_tiktok",
        "record_type": "raw_xhr",
        "api_url": api_url,
        "error": body.get("error"),
        "data_keys": list(body.keys())[:15] if isinstance(body, dict) else [],
    }


def is_verify_page(url: str, title: str) -> bool:
    low_u = (url or "").lower()
    low_t = (title or "").lower()
    return any(
        k in low_u or k in low_t
        for k in ("/verify/", "security check", "captcha", "punish", "/buyer/login")
    )


def collect_url(
    context: BrowserContext, target_url: str, wait_sec: int = 12
) -> dict[str, Any]:
    page = context.new_page()
    page.set_default_timeout(45000)

    captured_records: list[dict[str, Any]] = []
    raw_matches: list[dict[str, Any]] = []
    doc_status: int | None = None
    doc_date: str | None = None

    def on_response(resp: Response) -> None:
        nonlocal doc_status, doc_date
        u = resp.url
        try:
            if resp.request.resource_type == "document" and doc_status is None:
                doc_status = resp.status
                doc_date = resp.headers.get("date")
        except Exception:
            pass
        if not is_interesting_api(u) or resp.status != 200:
            return
        try:
            body = resp.json()
            if isinstance(body, dict):
                raw_matches.append(
                    {"api_url": u, "error": body.get("error"), "keys": list(body.keys())[:10]}
                )
                if not body.get("error"):
                    captured_records.append(classify_captured_response(u, body))
        except Exception:
            pass

    page.on("response", on_response)
    t0 = time.time()
    page.goto(target_url, wait_until="domcontentloaded", timeout=45000)

    # Đợi thông minh: kiểm tra mỗi 0.5s xem đã bắt được PDP/Search JSON hoặc dính verify chưa
    sdk_patched = False
    verify_hit = False
    deadline = time.time() + wait_sec
    while time.time() < deadline:
        cur_url = page.url
        cur_title = ""
        try:
            cur_title = page.title()
        except Exception:
            pass

        if is_verify_page(cur_url, cur_title):
            verify_hit = True
            break

        if not sdk_patched:
            try:
                sdk_patched = bool(
                    page.evaluate(
                        "() => { try { return !window.fetch.toString().includes('[native code]'); } catch { return false; } }"
                    )
                )
            except Exception:
                pass

        # Nếu là Lazada PDP DOM hoặc đã bắt được dữ liệu Shopee PDP/Search thì dừng sớm
        if any(r.get("record_type") in ("pdp", "search_list") for r in captured_records):
            time.sleep(1.0)
            break
        if "lazada.vn/products/" in cur_url and doc_status == 200 and (time.time() - t0) > 2.5:
            break
        time.sleep(0.5)

    final_url = page.url
    final_title = ""
    html = ""
    try:
        final_title = page.title()
        html = page.content()
    except Exception:
        pass

    dom_records: list[dict[str, Any]] = []
    if "lazada." in final_url and html:
        laz = parse_lazada_from_dom(html, final_url)
        if laz:
            dom_records.append(laz)
    if "tiktok." in final_url and html:
        tt = parse_tiktok_from_dom(html, final_url)
        if tt:
            dom_records.append(tt)

    clock_skew_sec = None
    if doc_date:
        try:
            srv_ts = email.utils.parsedate_to_datetime(doc_date).timestamp()
            clock_skew_sec = int(round(time.time() - srv_ts))
        except Exception:
            pass

    need_manual_action = verify_hit or is_verify_page(final_url, final_title)
    if need_manual_action:
        # Giữ nguyên tab trên màn hình Headful Chrome để người dùng tự login / xác minh tay
        try:
            page.bring_to_front()
        except Exception:
            pass
    else:
        page.close()

    return {
        "target_url": target_url,
        "final_url": final_url,
        "page_title": final_title,
        "http_status": doc_status,
        "elapsed_ms": int((time.time() - t0) * 1000),
        "sdk_fetch_patched": sdk_patched,
        "clock_skew_sec": clock_skew_sec,
        "verification_or_login_required": need_manual_action,
        "tab_kept_open_for_user": need_manual_action,
        "xhr_captured_count": len(captured_records),
        "structured_records": captured_records + dom_records,
        "raw_api_hits": raw_matches,
    }


def diagnose_session(context: BrowserContext) -> dict[str, Any]:
    """Kiểm tra sức khỏe phiên Chrome CDP (tài khoản Shopee, SDK fetch, đồng hồ)."""
    page = context.new_page()
    page.set_default_timeout(30000)
    diag: dict[str, Any] = {"checked_at_utc": datetime.now(UTC).isoformat()}
    try:
        page.goto("https://shopee.vn/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
        diag["shopee_url"] = page.url
        diag["shopee_title"] = page.title()
        diag["verify_redirected"] = is_verify_page(page.url, diag["shopee_title"])
        diag["sdk_fetch_patched"] = bool(
            page.evaluate(
                "() => { try { return !window.fetch.toString().includes('[native code]'); } catch { return false; } }"
            )
        )
        diag["user_agent"] = page.evaluate("() => navigator.userAgent")
        acc = page.evaluate(
            """async () => {
                try {
                    const r = await fetch('/api/v4/account/basic/get_account_info', {credentials: 'include'});
                    const j = await r.json().catch(() => null);
                    const d = (j && j.data) || {};
                    return {http_status: r.status, error: j && j.error, userid: d.userid || null, username: d.username || null};
                } catch (e) {
                    return {error: String(e)};
                }
            }"""
        )
        diag["shopee_account"] = acc
    finally:
        page.close()
    return diag


def listen_live_tabs(context: BrowserContext, duration_sec: int) -> list[dict[str, Any]]:
    """Chế độ Live Passive Sniffer trên toàn bộ tab của Chrome trong N giây."""
    collected: list[dict[str, Any]] = []

    def attach(p: Page) -> None:
        def on_resp(resp: Response) -> None:
            u = resp.url
            if not is_interesting_api(u) or resp.status != 200:
                return
            try:
                body = resp.json()
                if isinstance(body, dict) and not body.get("error"):
                    rec = classify_captured_response(u, body)
                    rec["captured_at_utc"] = datetime.now(UTC).isoformat()
                    collected.append(rec)
                    print(f"  [+] Bắt được {rec.get('platform')}/{rec.get('record_type')}: {u[:85]}")
            except Exception:
                pass

        p.on("response", on_resp)

    for existing_page in context.pages:
        attach(existing_page)
    context.on("page", attach)

    print(f"Đang lắng nghe thụ động trên {len(context.pages)} tab Chrome trong {duration_sec} giây...")
    print("Hãy tự do lướt hoặc mở sản phẩm Shopee / Lazada / TikTok Shop trên cửa sổ Chrome đó.")
    time.sleep(duration_sec)
    return collected


def _highlight_and_click(page: Page, locator: Any, label: str = "") -> None:
    """Cuộn tới phần tử, tô viền đỏ nổi bật để user quan sát rồi tự động click."""
    locator.scroll_into_view_if_needed(timeout=8000)
    try:
        locator.evaluate(
            """el => {
                el.style.outline = '3px solid #ef4444';
                el.style.outlineOffset = '2px';
                el.style.backgroundColor = 'rgba(254, 226, 226, 0.35)';
            }"""
        )
    except Exception:
        pass
    if label:
        print(f"  [AUTO-CLICK] {label}")
    page.wait_for_timeout(450)
    locator.click(timeout=10000)


def auto_click_crawl(
    context: BrowserContext,
    source: str = "all",
    max_items: int = 4,
    keyword: str = "chuột không dây logitech",
) -> list[dict[str, Any]]:
    """
    Chế độ Auto-Click Headful Crawler:
    Tự động mở trình duyệt, cuộn trang, highlight thẻ sản phẩm và click tuần tự
    vào từng sản phẩm để bóc tách dữ liệu thật mà không cần người dùng bấm tay.
    """
    results: list[dict[str, Any]] = []
    page = context.pages[0] if context.pages else context.new_page()
    page.set_default_timeout(30000)
    try:
        page.bring_to_front()
    except Exception:
        pass

    # --- 1. Auto-click trên LichSuGia.net (Shopee products + price_history) ---
    if source in ("all", "lichsugia"):
        print("\n[AUTO-CRAWL 1/3] Đang mở lichsugia.net và tự động click từng sản phẩm...")
        captured_net: dict[str, Any] = {}

        def on_net_resp(resp: Response) -> None:
            if "/backend-api/api/public/products/platform/" in resp.url and resp.status == 200:
                try:
                    captured_net["last"] = resp.json()
                except Exception:
                    pass

        page.on("response", on_net_resp)
        page.goto("https://lichsugia.net/", wait_until="domcontentloaded")
        page.wait_for_selector('a[href^="/product/"]', timeout=15000)
        page.wait_for_timeout(1200)

        # Lấy danh sách href duy nhất trên trang chủ để click tuần tự
        hrefs: list[str] = page.evaluate(
            """() => {
                const seen = new Set();
                const out = [];
                for (const a of document.querySelectorAll('a[href^="/product/"]')) {
                    const h = a.getAttribute('href');
                    if (h && !seen.has(h)) { seen.add(h); out.push(h); }
                }
                return out;
            }"""
        )

        for idx, href in enumerate(hrefs[:max_items], 1):
            captured_net.clear()
            loc = page.locator(f'a[href="{href}"]').first
            try:
                title_preview = (loc.inner_text(timeout=3000) or href).splitlines()[0][:55]
                _highlight_and_click(page, loc, f"lichsugia.net [{idx}/{min(max_items, len(hrefs))}]: {title_preview}")
                page.wait_for_url("**/product/**", timeout=12000)

                # Đợi ngắn cho XHR /backend-api/... hoặc gọi in-page fetch theo shop_id/item_id từ URL
                for _ in range(4):
                    if "last" in captured_net:
                        break
                    page.wait_for_timeout(400)

                d = captured_net.get("last") or {}
                if not d.get("name"):
                    m_id = re.search(r"-i\.(\d+)\.(\d+)", page.url)
                    if m_id:
                        try:
                            d = page.evaluate(
                                """async ([sid, iid]) => {
                                    const r = await fetch(`/backend-api/api/public/products/platform/${sid}/${iid}`);
                                    return r.ok ? await r.json() : {};
                                }""",
                                [m_id.group(1), m_id.group(2)],
                            )
                        except Exception:
                            d = {}
                if d.get("name"):
                    results.append(
                        {
                            "platform": "shopee (via lichsugia.net auto-click)",
                            "url": page.url,
                            "name": d.get("name"),
                            "shop_id": d.get("shop_id_platform"),
                            "item_id": d.get("product_id_platform"),
                            "price_vnd": d.get("price"),
                            "original_price_vnd": d.get("price_before_discount"),
                            "sold": d.get("sold"),
                            "rating_avg": round(float(d.get("rating_avg") or 0), 2),
                            "is_mall_shop": d.get("is_mall_shop"),
                            "history_points": len(d.get("price_history") or []),
                        }
                    )
                    print(
                        f"     -> Thu được: {d.get('name')[:45]} | {d.get('price')}đ | "
                        f"sold={d.get('sold')} | history={len(d.get('price_history') or [])} điểm"
                    )
                page.go_back(wait_until="domcontentloaded")
                page.wait_for_selector('a[href^="/product/"]', timeout=12000)
                page.wait_for_timeout(600)
            except Exception as exc:
                print(f"     [WARN] Bỏ qua {href[:40]}: {exc}")
                page.goto("https://lichsugia.net/", wait_until="domcontentloaded")
                page.wait_for_timeout(1000)
        page.remove_listener("response", on_net_resp)

    # --- 2. Auto-click trên GiaReVN.com (Shopee & Lazada products + priceChart) ---
    if source in ("all", "giarevn"):
        print("\n[AUTO-CRAWL 2/3] Đang mở giarevn.com và tự động click từng sản phẩm...")
        page.goto("https://giarevn.com/", wait_until="domcontentloaded")
        page.wait_for_selector(".product-card a.product-title", timeout=15000)
        page.wait_for_timeout(800)

        g_hrefs: list[str] = page.evaluate(
            """() => {
                const seen = new Set();
                const out = [];
                for (const a of document.querySelectorAll('.product-card a.product-title')) {
                    const h = a.getAttribute('href');
                    if (h && !seen.has(h)) { seen.add(h); out.push(h); }
                }
                return out;
            }"""
        )

        for idx, href in enumerate(g_hrefs[:max_items], 1):
            loc = page.locator(f'.product-card a.product-title[href="{href}"]').first
            try:
                title_preview = (loc.inner_text(timeout=3000) or href)[:55]
                _highlight_and_click(page, loc, f"giarevn.com [{idx}/{min(max_items, len(g_hrefs))}]: {title_preview}")
                page.wait_for_url("**/product/**", timeout=12000)
                # Đợi Astro server-island #priceChart nạp xong
                try:
                    page.wait_for_selector("#priceChart", timeout=8000)
                except Exception:
                    pass
                page.wait_for_timeout(600)

                extracted = page.evaluate(
                    """() => {
                        const h1 = document.querySelector('h1');
                        const canvas = document.querySelector('#priceChart');
                        const cur = document.querySelector('.current');
                        const hi = document.querySelector('.highest');
                        const lo = document.querySelector('.lowest');
                        return {
                            name: h1 ? h1.innerText.trim() : document.title,
                            current_text: cur ? cur.innerText.trim() : null,
                            highest_text: hi ? hi.innerText.trim() : null,
                            lowest_text: lo ? lo.innerText.trim() : null,
                            prices: canvas ? JSON.parse(canvas.getAttribute('data-prices') || '[]') : [],
                            labels: canvas ? JSON.parse(canvas.getAttribute('data-labels') || '[]') : [],
                        };
                    }"""
                )
                if extracted.get("name") and "không tìm thấy" not in extracted.get("name", "").lower():
                    results.append(
                        {
                            "platform": "shopee/lazada (via giarevn.com auto-click)",
                            "url": page.url,
                            "name": extracted.get("name"),
                            "price_vnd": extracted["prices"][-1] if extracted.get("prices") else None,
                            "price_history": extracted.get("prices"),
                            "price_dates": extracted.get("labels"),
                            "summary_text": {
                                "current": extracted.get("current_text"),
                                "highest": extracted.get("highest_text"),
                                "lowest": extracted.get("lowest_text"),
                            },
                        }
                    )
                    print(
                        f"     -> Thu được: {str(extracted.get('name'))[:45]} | "
                        f"prices={extracted.get('prices')}"
                    )
                page.go_back(wait_until="domcontentloaded")
                page.wait_for_selector(".product-card a.product-title", timeout=12000)
                page.wait_for_timeout(600)
            except Exception as exc:
                print(f"     [WARN] Bỏ qua {href[:40]}: {exc}")
                page.goto("https://giarevn.com/", wait_until="domcontentloaded")
                page.wait_for_timeout(1000)

    # --- 3. Auto-crawl trực tiếp Lazada PDP (và tự kiểm tra Shopee nếu đã login) ---
    if source in ("all", "lazada"):
        print("\n[AUTO-CRAWL 3/3] Đang mở trực tiếp trang sản phẩm Lazada (Headful)...")
        lazada_urls = [
            "https://www.lazada.vn/products/chuot-khong-day-logitech-m185-wireless-usbxam-den-hang-chinh-hang-i2174655511.html",
            "https://www.lazada.vn/products/chuot-khong-day-logitech-m331-den-i683118869.html",
            "https://www.lazada.vn/products/ban-phim-gaming-logitech-g213-prodigy-rgb-i1249690979.html",
        ]
        for idx, lurl in enumerate(lazada_urls[:max_items], 1):
            page.goto(lurl, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1200)
            # Cuộn và tô viền giá sản phẩm trên giao diện Lazada cho user thấy trực tiếp
            try:
                page.evaluate(
                    """() => {
                        const p = document.querySelector('.pdp-price_type_normal, .pdp-product-price, h1');
                        if (p) {
                            p.scrollIntoView({behavior: 'smooth', block: 'center'});
                            p.style.outline = '3px solid #16a34a';
                        }
                    }"""
                )
            except Exception:
                pass
            laz = parse_lazada_from_dom(page.content(), page.url)
            if laz:
                laz["platform"] = "lazada (direct headful auto-crawl)"
                results.append(laz)
                print(
                    f"  [LAZADA {idx}/{min(max_items, len(lazada_urls))}] "
                    f"{str(laz.get('name'))[:48]} -> {laz.get('price_vnd')}đ"
                )
            page.wait_for_timeout(700)

    if source == "shopee":
        print(f"\n[AUTO-CRAWL SHOPEE] Tìm kiếm '{keyword}' trên Shopee...")
        search_url = f"https://shopee.vn/search?keyword={urllib.parse.quote(keyword)}"
        res = collect_url(context, search_url, wait_sec=12)
        results.extend(res.get("structured_records") or [])
        if res.get("verification_or_login_required"):
            print(
                "[SHOPEE CẦN LOGIN] Tab Shopee đang được giữ mở trên cửa sổ Chrome 9222 "
                "để bạn đăng nhập 1 lần."
            )

    return results


def open_login_tabs(context: BrowserContext) -> list[str]:
    """Mở sẵn các tab đăng nhập Shopee, TikTok, Lazada trên cửa sổ Chrome Headful 9222."""
    urls = [
        "https://shopee.vn/buyer/login",
        "https://www.tiktok.com/login",
        "https://www.lazada.vn/",
    ]
    opened: list[str] = []
    for u in urls:
        p = context.new_page()
        p.goto(u, wait_until="domcontentloaded", timeout=30000)
        opened.append(p.url)
    try:
        context.pages[0].bring_to_front()
    except Exception:
        pass
    print("[OPEN-LOGIN] Đã mở các tab đăng nhập trên cửa sổ Chrome Headful.")
    print("Hãy đăng nhập trực tiếp trên Chrome, sau đó chạy lại `--diagnose` hoặc `--url`.")
    return opened


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mode C (v2.0 - Headful) - Chrome CDP Collector cho Shopee, Lazada, TikTok Shop"
    )
    parser.add_argument("--url", nargs="+", help="Một hoặc nhiều URL sản phẩm/tìm kiếm")
    parser.add_argument(
        "--listen", type=int, default=0, help="Chế độ Live Passive Sniffer trong N giây"
    )
    parser.add_argument(
        "--diagnose", action="store_true", help="Kiểm tra sức khỏe phiên Chrome CDP"
    )
    parser.add_argument(
        "--open-login",
        action="store_true",
        help="Mở sẵn Chrome Headful với các tab đăng nhập Shopee/TikTok/Lazada để user tự login",
    )
    parser.add_argument(
        "--auto-crawl",
        action="store_true",
        help="Tự động cuộn trang, highlight và click tuần tự từng sản phẩm trên Chrome Headful",
    )
    parser.add_argument(
        "--source",
        default="all",
        choices=["all", "lichsugia", "giarevn", "lazada", "shopee"],
        help="Nguồn dùng cho --auto-crawl (mặc định: all)",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=3,
        help="Số sản phẩm tự động click tối đa mỗi nguồn khi chạy --auto-crawl (mặc định: 3)",
    )
    parser.add_argument(
        "--keyword",
        default="chuột không dây logitech",
        help="Từ khóa tìm kiếm khi chạy --auto-crawl --source shopee",
    )
    parser.add_argument("--cdp", default="http://127.0.0.1:9222", help="Endpoint Chrome CDP")
    parser.add_argument("--profile", default=DEFAULT_PROFILE_DIR, help="Thư mục Chrome Profile")
    parser.add_argument("--wait", type=int, default=12, help="Số giây tối đa đợi mỗi URL")
    parser.add_argument(
        "--no-launch", action="store_true", help="Không tự bật Chrome nếu cổng CDP chưa mở"
    )
    args = parser.parse_args()

    if (
        not args.url
        and not args.listen
        and not args.diagnose
        and not args.open_login
        and not args.auto_crawl
    ):
        parser.print_help()
        return

    cdp_boot = ensure_chrome_cdp_running(
        args.cdp, profile_dir=args.profile, auto_launch=not args.no_launch
    )
    print(
        f"[CDP READY - HEADFUL] already_running={cdp_boot['already_running']}, "
        f"browser={cdp_boot['version_info'].get('Browser')}"
    )

    output: dict[str, Any] = {
        "collected_at_utc": datetime.now(UTC).isoformat(),
        "cdp_endpoint": args.cdp,
        "cdp_boot": cdp_boot,
    }

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(args.cdp)
        context = browser.contexts[0] if browser.contexts else browser.new_context()

        if args.open_login:
            output["opened_login_tabs"] = open_login_tabs(context)

        if args.diagnose:
            output["diagnosis"] = diagnose_session(context)
            print("[DIAGNOSIS]", json.dumps(output["diagnosis"], ensure_ascii=False, indent=2))

        if args.auto_crawl:
            output["auto_crawl_records"] = auto_click_crawl(
                context,
                source=args.source,
                max_items=args.max_items,
                keyword=args.keyword,
            )
            print(f"[AUTO-CRAWL DONE] Tổng số bản ghi thu được: {len(output['auto_crawl_records'])}")

        if args.url:
            results = []
            for target in args.url:
                res = collect_url(context, target, wait_sec=args.wait)
                results.append(res)
                print(
                    f"[URL] {target[:65]} -> status={res['http_status']}, "
                    f"verify={res['verification_or_login_required']}, "
                    f"records={len(res['structured_records'])}"
                )
                if res["verification_or_login_required"]:
                    print(
                        "[DỪNG AN TOÀN] Tab yêu cầu đăng nhập/xác minh đang được giữ mở "
                        "trên cửa sổ Chrome 9222. Hãy thao tác tay trên Chrome rồi chạy lại!"
                    )
                    break
            output["url_results"] = results

        if args.listen > 0:
            output["live_listen_records"] = listen_live_tabs(context, args.listen)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Đã lưu kết quả Mode C tại: {OUT_FILE}")


if __name__ == "__main__":
    main()
