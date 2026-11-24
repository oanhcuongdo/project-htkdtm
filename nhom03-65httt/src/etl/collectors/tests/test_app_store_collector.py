import argparse
import csv
import hashlib
import sys
from pathlib import Path

import pytest


COLLECTOR_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(COLLECTOR_DIR))

import app_store_collector as collector  # noqa: E402


def test_normalize_review_preserves_rss_fields_and_guesses_vietnamese() -> None:
    entry = {
        "id": {"label": "sample-review-001"},
        "im:rating": {"label": "5"},
        "content": {"label": "Ứng dụng này rất hữu ích!"},
        "im:version": {"label": "3.1.0"},
        "im:voteSum": {"label": "7"},
        "author": {"name": {"label": "Người dùng mẫu"}},
    }

    row = collector.normalize_review(entry, "sample-platform", "2026-11-23T00:00:00+00:00")

    assert row["rating"] == 5
    assert row["app_version"] == "3.1.0"
    assert row["thumbs_up"] == 7
    assert row["author_hash"] == hashlib.sha256("Người dùng mẫu".encode()).hexdigest()[:12]
    assert len(row["author_hash"]) == 12
    assert row["lang_guess"] == "vi"


def test_normalize_review_leaves_author_hash_blank_without_author_name() -> None:
    row = collector.normalize_review(
        {"id": {"label": "sample-review-002"}, "author": {"name": {"label": ""}}},
        "sample-platform",
        "2026-11-23T00:00:00+00:00",
    )

    assert row["author_hash"] == ""


def test_read_existing_ids_reads_csv_ids_and_rejects_wrong_header(tmp_path: Path) -> None:
    csv_path = tmp_path / "reviews.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=collector.CSV_COLUMNS)
        writer.writeheader()
        writer.writerow({"review_id": "sample-review-001"})
        writer.writerow({"review_id": "sample-review-002"})

    assert collector.read_existing_ids(csv_path) == {"sample-review-001", "sample-review-002"}

    csv_path.write_text("wrong,header\nvalue,value\n", encoding="utf-8")
    with pytest.raises(collector.CollectorError, match="không có đúng tiêu đề CSV"):
        collector.read_existing_ids(csv_path)


def test_collect_writes_60_unique_rows_and_adds_none_on_rerun(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    platforms_file = tmp_path / "platforms.yml"
    platforms_file.write_text(
        collector.yaml.safe_dump(
            {
                "platforms": [
                    {
                        "id": "sample-platform",
                        "play_id": "sample.play.id",
                        "ios_id": "123456",
                        "platform_group": "sample",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(collector, "PLATFORMS_FILE", platforms_file)
    monkeypatch.setattr(collector.time, "sleep", lambda _seconds: None)

    entries = [
        {
            "id": {"label": f"sample-review-{index:03d}"},
            "im:rating": {"label": "5"},
            "content": {"label": "Ứng dụng mẫu rất hữu ích"},
            "im:version": {"label": "3.1.0"},
            "im:voteSum": {"label": str(index)},
            "author": {"name": {"label": f"Người dùng {index}"}},
        }
        for index in range(60)
    ]

    def fake_request_page(_app_id: str, page: int, _base_delay: float):
        start = (page - 1) * 50
        return entries[start : start + 50]

    monkeypatch.setattr(collector, "request_page", fake_request_page)
    args = argparse.Namespace(
        only="sample-platform", count=60, out=tmp_path / "out", sleep=2
    )

    csv_path, added_count, _requested_count = collector.collect(args)
    assert added_count == 60

    csv_path, added_count, _requested_count = collector.collect(args)
    assert added_count == 0

    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)

    assert reader.fieldnames == collector.CSV_COLUMNS
    assert len(rows) == 60
    assert len({row["review_id"] for row in rows}) == 60
    assert all(row["app_version"] for row in rows)
    assert all(row["thumbs_up"] for row in rows)
