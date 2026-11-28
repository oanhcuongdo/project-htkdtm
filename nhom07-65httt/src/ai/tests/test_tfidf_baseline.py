import csv
import json

import pytest

from src.recommendations.evaluate_tfidf import evaluate
from src.recommendations.tfidf_baseline import (
    CourseDocument,
    LearnerProfile,
    TfidfBaseline,
)


def test_tfidf_cosine_matches_vietnamese_english_and_course_skills():
    ranker = TfidfBaseline(
        [
            CourseDocument(
                "python",
                "Lập trình Python",
                description="Phân tích dữ liệu với Python",
                direct_skills=("python", "data analysis"),
            ),
            CourseDocument(
                "design",
                "Thiết kế giao diện",
                description="UI UX cho ứng dụng web",
                skills=("figma",),
            ),
        ]
    )

    results = ranker.rank(
        LearnerProfile(
            "learner-1",
            goals=("Phân tích dữ liệu",),
            current_skills=("Python",),
        ),
        top_k=2,
    )

    assert [result.course.course_id for result in results] == ["python", "design"]
    assert results[0].score > 0
    assert 0 <= results[0].score <= 1
    assert results[0].ranking_method == "tfidf_cosine"
    assert results[1].score == 0


def test_cold_start_and_no_match_use_deterministic_popularity_fallback():
    ranker = TfidfBaseline(
        [
            CourseDocument("b", "Python cơ bản", popularity_score=4),
            CourseDocument("a", "Python nâng cao", popularity_score=4),
            CourseDocument("c", "Python thực hành", popularity_score=1),
        ]
    )

    cold_start = ranker.rank(LearnerProfile("cold"), top_k=2)
    no_match = ranker.rank(
        LearnerProfile("unmatched", goals=("nghề làm bánh",)), top_k=2
    )

    assert [result.course.course_id for result in cold_start] == ["a", "b"]
    assert all(result.fallback_reason == "cold_start" for result in cold_start)
    assert all(result.fallback_reason == "no_tfidf_match" for result in no_match)
    assert all(result.score == 0 for result in (*cold_start, *no_match))


def test_candidate_pool_and_input_order_do_not_change_tfidf_ranking():
    courses = [
        CourseDocument("z", "Học Python cho phân tích dữ liệu"),
        CourseDocument("a", "Python phân tích dữ liệu"),
        CourseDocument("other", "Thiết kế đồ họa"),
    ]
    profile = LearnerProfile(
        "learner",
        goals=("phân tích dữ liệu",),
        candidate_course_ids=("z", "a"),
    )

    first = TfidfBaseline(courses).rank(profile, top_k=5)
    second = TfidfBaseline(list(reversed(courses))).rank(profile, top_k=5)

    assert [item.course.course_id for item in first] == ["a", "z"]
    assert [(item.course.course_id, item.score) for item in first] == [
        (item.course.course_id, item.score) for item in second
    ]


def test_invalid_catalog_and_profile_inputs_fail_explicitly():
    with pytest.raises(ValueError, match="unique"):
        TfidfBaseline(
            [CourseDocument("same", "Python"), CourseDocument("same", "SQL")]
        )

    ranker = TfidfBaseline([CourseDocument("python", "Python cơ bản")])
    with pytest.raises(ValueError, match="unknown courses"):
        ranker.rank(
            LearnerProfile("learner", candidate_course_ids=("missing",))
        )
    with pytest.raises(ValueError, match="at least 1"):
        ranker.rank(LearnerProfile("learner"), top_k=0)


def test_evaluator_exports_top_k_for_every_profile_and_reproducibility_metadata(
    tmp_path,
):
    courses_path = tmp_path / "courses.json"
    profiles_path = tmp_path / "profiles.json"
    output_path = tmp_path / "m0.csv"
    courses_path.write_text(
        json.dumps(
            [
                {
                    "course_id": "python",
                    "title": "Python phân tích dữ liệu",
                    "description": None,
                    "direct_skills": [{"skill_id": "python", "source": "verified"}],
                    "popularity_score": 2,
                    "approval_status": "approved",
                    "offer_type": "INTERNAL",
                    "price_amount": 1000,
                    "price_currency": "VND",
                    "required_hours_per_week": 3,
                    "prerequisite_course_ids": [],
                },
                {
                    "course_id": "sql",
                    "title": "SQL cơ bản",
                    "skills": ["database"],
                    "popularity_score": 3,
                    "approval_status": "approved",
                    "offer_type": "INTERNAL",
                    "price_amount": 1000,
                    "price_currency": "VND",
                    "required_hours_per_week": 3,
                    "prerequisite_course_ids": [],
                },
            ]
        ),
        encoding="utf-8",
    )
    profiles_path.write_text(
        json.dumps(
            [
                {
                    "learner_key": "learner-1",
                    "goals": [{"goal_id": "data-analyst", "label": "phân tích dữ liệu"}],
                    "current_skills": [{"skill_id": "python"}],
                    "constraints": {
                        "allowed_offer_types": ["INTERNAL"],
                        "purchased_course_ids": [],
                        "enrolled_course_ids": [],
                        "completed_course_ids": [],
                        "exclude_course_ids": [],
                        "exclude_enrolled_or_completed": True,
                        "max_budget_amount": 10000,
                        "currency": "VND",
                        "available_hours_per_week": 5,
                    },
                },
                {
                    "learner_key": "learner-2",
                    "goals": None,
                    "current_skills": None,
                    "candidate_course_ids": [],
                    "constraints": {
                        "allowed_offer_types": ["INTERNAL"],
                        "purchased_course_ids": [],
                        "enrolled_course_ids": [],
                        "completed_course_ids": [],
                        "exclude_course_ids": [],
                        "exclude_enrolled_or_completed": True,
                        "max_budget_amount": 10000,
                        "currency": "VND",
                        "available_hours_per_week": 5,
                    },
                },
            ]
        ),
        encoding="utf-8",
    )

    metadata_path = evaluate(
        courses_path=courses_path,
        profiles_path=profiles_path,
        output_path=output_path,
        dataset_version_id="dataset-test-v1",
        top_k=1,
    )

    with output_path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert [row["learner_key"] for row in rows] == ["learner-1", "learner-2"]
    assert rows[0]["course_id"] == "python"
    assert rows[0]["score_scale"] == "cosine_0_to_1"
    assert rows[1]["ranking_method"] == "no_eligible_candidates"
    assert metadata["deterministic"] is True
    assert metadata["profiles"]["count"] == 2
    assert metadata["output"]["profiles"][1]["result_count"] == 0
    assert metadata["output"]["profiles"][0]["eligible_candidate_ids"] == [
        "python",
        "sql",
    ]
    assert metadata["output"]["profiles"][0]["prerequisite_violations"] == 0
    assert metadata["output"]["profiles"][0]["missing_fields_warning"] == []
    assert metadata["vectorizer_config"]["ngram_range"] == [1, 2]

    original_output = output_path.read_bytes()
    original_metadata = metadata_path.read_bytes()
    evaluate(
        courses_path=courses_path,
        profiles_path=profiles_path,
        output_path=output_path,
        dataset_version_id="dataset-test-v1",
        top_k=1,
    )

    assert output_path.read_bytes() == original_output
    assert metadata_path.read_bytes() == original_metadata

