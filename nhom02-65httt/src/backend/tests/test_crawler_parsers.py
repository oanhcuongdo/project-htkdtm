"""Unit tests for crawler parsers and verified sample crawl payload."""

from __future__ import annotations

import json
from pathlib import Path

from app.crawler.multi_platform_crawler import _parse_vnd


def test_parse_vnd_handles_various_formats() -> None:
    assert _parse_vnd("285.000 ₫") == 285000
    assert _parse_vnd("1.189.000 đ") == 1189000
    assert _parse_vnd(350000) == 350000
    assert _parse_vnd(349000.0) == 349000
    assert _parse_vnd("") is None
    assert _parse_vnd(None) is None


def test_verified_crawl_sample_payload_is_valid() -> None:
    sample_path = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "crawler"
        / "samples"
        / "verified_crawl_output.json"
    )
    assert sample_path.is_file()
    data = json.loads(sample_path.read_text(encoding="utf-8"))

    expected_keys = {
        "lazada_direct_pdp",
        "shopee_via_history_apis",
        "tiki_open_api",
        "giarevn_chart_sample",
        "retail_benchmarks",
    }
    assert expected_keys.issubset(data.keys())
    assert len(data["lazada_direct_pdp"]) >= 1
    assert len(data["shopee_via_history_apis"]) >= 1
    assert len(data["tiki_open_api"]) >= 1
