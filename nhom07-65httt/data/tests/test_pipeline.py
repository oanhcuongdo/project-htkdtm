import csv
import json
import shutil
from contextlib import contextmanager
from itertools import count
import unittest
from pathlib import Path

from pipeline.cleaner import clean_text
from pipeline.database_loader import load_release
from pipeline.deduplicate import deduplicate
from pipeline.normalize import canonical_course_url, duration_to_minutes, normalize_course
from pipeline.quality_check import check_quality
from pipeline.raw_ingest import ingest_legacy_csv
from pipeline.release import create_release, validate_approved
from pipeline.skill_mapping import load_taxonomy, map_skills
from pipeline.storage import read_jsonl
from pipeline.transform import transform_batch


_TEMP_COUNTER = count()


@contextmanager
def workspace_tempdir():
    root = Path(__file__).parent / ".test_tmp"
    root.mkdir(exist_ok=True)
    path = root / f"case-{next(_TEMP_COUNTER)}"
    path.mkdir()
    try:
        yield path
    finally:
        shutil.rmtree(path)


def raw_record(**overrides):
    source = {
        "course_id": "python-basics",
        "title": "Python &amp; Data Basics",
        "url": "https://www.udemy.com/course/python-basics/?ref=campaign",
        "duration": "2h 15m",
        "rating": "4.5",
        "rating_count": "18",
        "scraped_at": "2026-11-18T09:00:00+00:00",
        "description": "A public description.",
        "skills": "Python; Data analysis",
        "level": "Beginner",
    }
    source.update(overrides)
    return {"source_name": "udemy", "source_url": source.get("url"), "crawled_at": source.get("scraped_at"), "raw_payload": source}


class CleanerAndNormalizerTests(unittest.TestCase):
    def test_clean_text_decodes_html_strips_tags_and_normalizes_unicode(self):
        self.assertEqual(clean_text("<b>Caf&eacute;</b>  &amp;  data"), "Café & data")
        self.assertEqual(clean_text("Cafe\u0301"), "Café")
        self.assertIsNone(clean_text("  "))

    def test_duration_requires_explicit_units(self):
        self.assertEqual(duration_to_minutes("2h 15m"), 135)
        self.assertEqual(duration_to_minutes("45m"), 45)
        self.assertEqual(duration_to_minutes("2h"), 120)
        self.assertIsNone(duration_to_minutes("about two hours"))
        self.assertIsNone(duration_to_minutes(None))

    def test_canonical_url_drops_tracking_and_rejects_foreign_hosts(self):
        self.assertEqual(canonical_course_url("https://www.udemy.com/course/x/?ref=a"), "https://www.udemy.com/course/x/")
        self.assertIsNone(canonical_course_url("https://example.com/course/x/"))
        self.assertIsNone(canonical_course_url("javascript://www.udemy.com/course/x/"))

    def test_normalize_preserves_source_and_missing_values_as_null(self):
        record = normalize_course(raw_record(price="", currency="", description=""))
        self.assertEqual(record["title"], "Python & Data Basics")
        self.assertEqual(record["duration_minutes"], 135)
        self.assertEqual(record["price_amount"], None)
        self.assertEqual(record["description"], None)
        self.assertEqual(record["raw_description"], None)
        self.assertEqual(record["offer_type"], "EXTERNAL_REFERENCE")
        self.assertEqual(record["source_metadata"]["title"], "Python &amp; Data Basics")


class SkillAndQualityTests(unittest.TestCase):
    def test_taxonomy_maps_direct_and_marks_inferred_for_review(self):
        with workspace_tempdir() as temporary:
            taxonomy_path = temporary / "taxonomy.yaml"
            taxonomy_path.write_text("skills:\n  - name: Python\n    aliases: [py]\n    keywords: [Python]\n  - name: Data analysis\n    aliases: [analytics]\n    keywords: [data analysis]\n", encoding="utf-8")
            taxonomy = load_taxonomy(taxonomy_path)
        record = normalize_course(raw_record(skills="py", title="Python and data analysis"))
        mapped = map_skills(record, taxonomy)
        self.assertEqual(mapped["direct_skills"], ["Python"])
        self.assertEqual(mapped["inferred_skills"][0]["skill"], "Data analysis")
        self.assertTrue(mapped["inferred_skills"][0]["review_required"])

    def test_unconfigured_taxonomy_does_not_infer_skills(self):
        record = map_skills(normalize_course(raw_record(skills="")), None)
        self.assertIsNone(record["skills"])
        self.assertIsNone(record["inferred_skills"])

    def test_quality_blocks_missing_description_or_invalid_url(self):
        record = normalize_course(raw_record(description=""))
        checked = check_quality(record)
        self.assertEqual(checked["quality_status"], "needs_review")
        self.assertIn("missing_description", checked["quality_flags"])
        bad = normalize_course(raw_record(url="https://example.com/course/python-basics/"))
        self.assertEqual(check_quality(bad)["quality_status"], "rejected")


class DeduplicationTests(unittest.TestCase):
    def test_exact_duplicate_is_flagged_but_not_deleted(self):
        first = normalize_course(raw_record())
        duplicate = normalize_course(raw_record())
        rows, pairs = deduplicate([first, duplicate])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["duplicate_status"], "exact_duplicate")
        self.assertEqual(pairs, [])

    def test_near_duplicate_is_flagged_and_kept(self):
        first = normalize_course(raw_record(course_id="python-basics-a", title="Python Data Analysis Basics", url="https://www.udemy.com/course/python-basics-a/"))
        second = normalize_course(raw_record(course_id="python-basics-b", title="Python Data Analysis Basic", url="https://www.udemy.com/course/python-basics-b/"))
        rows, pairs = deduplicate([first, second])
        self.assertEqual(len(rows), 2)
        self.assertGreaterEqual(len(pairs), 1)
        self.assertEqual({row["duplicate_status"] for row in rows}, {"near_duplicate"})


class StorageAndReleaseTests(unittest.TestCase):
    def test_legacy_ingest_is_verbatim_and_does_not_change_csv(self):
        with workspace_tempdir() as temporary:
            root = temporary
            source = root / "courses.csv"
            source.write_text("course_id,title,url,scraped_at\nx,Example,https://www.udemy.com/course/x/,2026-01-01T00:00:00Z\n", encoding="utf-8")
            original_bytes = source.read_bytes()
            batch_id, batch_dir = ingest_legacy_csv(source, root / "raw")
            self.assertEqual(source.read_bytes(), original_bytes)
            manifest = json.loads((batch_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["total_records"], 1)
            self.assertFalse(manifest["raw_html_or_source_json_retained"])
            record = next(read_jsonl(batch_dir / "records.jsonl"))
            self.assertEqual(record["raw_payload"]["title"], "Example")
            self.assertTrue(batch_id.startswith("legacy-"))

    def test_transform_stages_rows_and_never_approves_missing_fields(self):
        with workspace_tempdir() as temporary:
            root = temporary
            source = root / "courses.csv"
            source.write_text("course_id,title,url,scraped_at\nx,Example,https://www.udemy.com/course/x/,2026-01-01T00:00:00Z\n", encoding="utf-8")
            batch_id, batch_dir = ingest_legacy_csv(source, root / "raw")
            summary = transform_batch(batch_dir, root / "staging", root / "approved", root / "reports")
            self.assertEqual(summary["records_staged"], 1)
            self.assertEqual(summary["approved_candidates"], 0)
            self.assertEqual(summary["quality_status_counts"], {"needs_review": 1})
            self.assertEqual(len(list(read_jsonl(root / "staging" / batch_id / "courses.jsonl"))), 1)
            self.assertEqual(list(read_jsonl(root / "approved" / batch_id / "courses.jsonl")), [])

    def test_release_only_accepts_approved_records_and_database_dry_run_writes_nothing(self):
        with workspace_tempdir() as temporary:
            root = temporary
            approved = root / "approved" / "batch"
            approved.mkdir(parents=True)
            row = map_skills(normalize_course(raw_record()), None)
            row = check_quality(row)
            self.assertEqual(row["quality_status"], "approved_candidate")
            from pipeline.storage import write_jsonl_new

            write_jsonl_new(approved / "courses.jsonl", [row])
            metadata = create_release(root / "approved", root / "releases", "1.0.0")
            self.assertEqual(metadata["approved_records"], 1)
            result = load_release(root / "releases" / "1.0.0", {"adapter": None}, dry_run=True)
            self.assertEqual(result["status"], "DRY_RUN")
            self.assertEqual(result["records_written"], 0)
            self.assertTrue(validate_approved(row)[0])

    def test_empty_release_has_full_schema_and_is_marked_empty(self):
        with workspace_tempdir() as temporary:
            root = temporary
            metadata = create_release(root / "approved", root / "releases", "0.0.1")
            self.assertEqual(metadata["release_status"], "EMPTY")
            with (root / "releases" / "0.0.1" / "courses.csv").open(encoding="utf-8-sig", newline="") as stream:
                self.assertIn("description", next(csv.reader(stream)))

    def test_internal_seed_has_five_original_courses_with_complete_quizzes(self):
        seed_path = Path(__file__).parents[1] / "data" / "internal" / "courses.json"
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        self.assertEqual(len(seed["courses"]), 5)
        for course in seed["courses"]:
            self.assertEqual(course["offer_type"], "INTERNAL")
            self.assertGreaterEqual(len(course["lessons"]), 2)
            self.assertLessEqual(len(course["lessons"]), 3)
            self.assertEqual(len(course["quiz"]), 10)
            self.assertTrue(all(0 <= item["answer_index"] < len(item["options"]) for item in course["quiz"]))


if __name__ == "__main__":
    unittest.main()
