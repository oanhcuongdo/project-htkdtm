from pathlib import Path
from typing import Sequence

import pytest

from src.recommendations.candidate_filter import (
    CourseCandidate,
    StudentProfile,
    filter_candidates,
)
from src.recommendations.m1_semantic import M1SemanticRanker
from src.recommendations.m2_hybrid import M2HybridRanker
from src.recommendations.tfidf_baseline import (
    CourseDocument,
    LearnerProfile,
    TfidfBaseline,
)


VERSION_ID = "dataset-filter-v1"


def course_candidate(course_id: str, **overrides) -> CourseCandidate:
    fields = {
        "course_id": course_id,
        "approval_status": "approved",
        "offer_type": "INTERNAL",
        "price_amount": 500.0,
        "price_currency": "VND",
        "required_hours_per_week": 3.0,
        "popularity_score": 1.0,
    }
    fields.update(overrides)
    return CourseCandidate(**fields)


def complete_filter_profile(**overrides) -> StudentProfile:
    fields = {
        "goals": ("data analyst",),
        "current_skills": ("Python",),
        "target_level": "BEGINNER",
        "allowed_offer_types": ("INTERNAL",),
        "purchased_course_ids": (),
        "enrolled_course_ids": (),
        "completed_course_ids": ("prereq-course",),
        "exclude_course_ids": (),
        "exclude_enrolled_or_completed": True,
        "max_budget_amount": 1000.0,
        "budget_currency": "VND",
        "available_hours_per_week": 5.0,
    }
    fields.update(overrides)
    return StudentProfile(**fields)


def test_filters_all_hard_constraints_and_requires_verified_prerequisites():
    candidates = [
        course_candidate("eligible"),
        course_candidate("pending", approval_status="pending_review"),
        course_candidate("external", offer_type="EXTERNAL_REFERENCE"),
        course_candidate("expensive", price_amount=1500),
        course_candidate("too-many-hours", required_hours_per_week=6),
        course_candidate("purchased"),
        course_candidate("enrolled"),
        course_candidate("already-completed"),
        course_candidate("unmet-prereq"),
        course_candidate("met-prereq"),
        course_candidate("unknown-prereq"),
    ]
    profile = complete_filter_profile(
        purchased_course_ids=("purchased",),
        enrolled_course_ids=("enrolled",),
        completed_course_ids=("prereq-course", "already-completed"),
    )
    prerequisites = {
        candidate.course_id: ()
        for candidate in candidates
    }
    prerequisites["unmet-prereq"] = ("missing-course",)
    prerequisites["met-prereq"] = ("prereq-course",)
    prerequisites["unknown-prereq"] = None

    result = filter_candidates(
        candidates,
        profile,
        prerequisites,
        fallback_limit=10,
        dataset_version_id=VERSION_ID,
    )

    assert result.eligible_candidate_ids == ("eligible", "met-prereq")
    assert result.prerequisite_violations == 0
    assert result.dataset_version_id == VERSION_ID
    rejection_reasons = {
        rejection.course_id: rejection.reasons
        for rejection in result.rejected_candidates
    }
    assert "not_approved" in rejection_reasons["pending"]
    assert "offer_type_not_allowed" in rejection_reasons["external"]
    assert "over_budget" in rejection_reasons["expensive"]
    assert "over_available_hours" in rejection_reasons["too-many-hours"]
    assert "already_purchased" in rejection_reasons["purchased"]
    assert "already_enrolled" in rejection_reasons["enrolled"]
    assert "already_completed" in rejection_reasons["already-completed"]
    assert "unmet_prerequisites" in rejection_reasons["unmet-prereq"]
    assert "unknown_course_prerequisites" in rejection_reasons["unknown-prereq"]
    assert "course_prerequisites.unknown-prereq" in result.missing_fields_warning


def test_missing_optional_profile_filters_keep_candidates_and_warn():
    profile = StudentProfile(
        goals=None,
        current_skills=None,
        target_level=None,
        allowed_offer_types=None,
        purchased_course_ids=None,
        enrolled_course_ids=None,
        completed_course_ids=None,
        exclude_course_ids=None,
        exclude_enrolled_or_completed=None,
        max_budget_amount=None,
        budget_currency=None,
        available_hours_per_week=None,
    )
    candidates = [
        course_candidate("low", popularity_score=1),
        course_candidate("high", popularity_score=5),
        course_candidate(
            "unknown-budget",
            price_amount=100000,
            popularity_score=3,
        ),
        course_candidate(
            "unknown-time",
            required_hours_per_week=100,
            popularity_score=4,
        ),
        course_candidate(
            "unknown-type",
            offer_type="EXTERNAL_REFERENCE",
            popularity_score=2,
        ),
    ]

    result = filter_candidates(
        candidates,
        profile,
        {candidate.course_id: () for candidate in candidates},
        dataset_version_id=VERSION_ID,
        fallback_limit=1,
    )

    assert result.eligible_candidate_ids == (
        "high",
        "low",
        "unknown-budget",
        "unknown-time",
        "unknown-type",
    )
    assert [candidate.course_id for candidate in result.fallback_candidates] == ["high"]
    assert result.fallback_reason == "cold_start"
    assert {
        "profile.allowed_offer_types",
        "profile.purchased_course_ids",
        "profile.exclude_course_ids",
        "profile.exclude_enrolled_or_completed",
        "profile.max_budget_amount",
        "profile.available_hours_per_week",
    }.issubset(result.missing_fields_warning)


def test_unknown_completion_history_fails_closed_for_courses_with_prerequisites():
    candidates = [
        course_candidate("requires-prereq"),
        course_candidate("no-prereq"),
    ]
    result = filter_candidates(
        candidates,
        complete_filter_profile(completed_course_ids=None),
        {
            "requires-prereq": ("previous-course",),
            "no-prereq": (),
        },
        dataset_version_id=VERSION_ID,
    )

    assert result.eligible_candidate_ids == ("no-prereq",)
    assert result.prerequisite_violations == 0
    assert "profile.completed_course_ids" in result.missing_fields_warning
    assert "unknown_completion_history" in result.rejected_candidates[0].reasons


def test_unknown_price_or_weekly_load_is_not_allowed_to_bypass_known_constraints():
    result = filter_candidates(
        [
            course_candidate("unknown-price", price_amount=None, price_currency=None),
            course_candidate("unknown-load", required_hours_per_week=None),
        ],
        complete_filter_profile(),
        {"unknown-price": (), "unknown-load": ()},
        dataset_version_id=VERSION_ID,
    )

    assert result.eligible_candidate_ids == ()
    assert result.fallback_candidates == ()
    assert result.fallback_reason == "no_eligible_candidates"
    assert {
        "courses.unknown-price.price",
        "courses.unknown-load.required_hours_per_week",
    }.issubset(result.missing_fields_warning)


def test_filter_result_is_shared_by_m0_m1_and_m2(tmp_path: Path):
    candidates = (
        course_candidate("allowed"),
        course_candidate("pending", approval_status="pending_review"),
    )
    filter_result = filter_candidates(
        candidates,
        complete_filter_profile(allowed_offer_types=None),
        {"allowed": (), "pending": ()},
        dataset_version_id=VERSION_ID,
    )
    documents = (
        CourseDocument("allowed", "Python for analytics"),
        CourseDocument("pending", "Python for pending course"),
    )
    learner = LearnerProfile(
        "learner-1",
        goals=("Python",),
    )

    m0_results = TfidfBaseline(
        documents,
        dataset_version_id=VERSION_ID,
    ).rank(
        learner,
        candidate_filter_result=filter_result,
    )
    m1_results = M1SemanticRanker(
        cache_dir=tmp_path / "m1",
        encoder=FakeEncoder(),
    ).rank(
        dataset_version_id=VERSION_ID,
        courses=documents,
        profile=learner,
        candidate_filter_result=filter_result,
    )
    m2_results = M2HybridRanker(
        M1SemanticRanker(
            cache_dir=tmp_path / "m2",
            encoder=FakeEncoder(),
        )
    ).rank(
        dataset_version_id=VERSION_ID,
        courses=documents,
        profile=learner,
        target_skills=(),
        current_skill_ids=(),
        target_level=None,
        skill_prerequisites={"allowed": (), "pending": ()},
        candidate_filter_result=filter_result,
    )

    assert tuple(item.course.course_id for item in m0_results) == ("allowed",)
    assert m1_results.eligible_candidate_ids == filter_result.eligible_candidate_ids
    assert tuple(item.course.course_id for item in m2_results.ranked_courses) == (
        "allowed",
    )
    assert m1_results.candidate_set_hash == filter_result.candidate_set_hash
    assert m2_results.candidate_set_hash == filter_result.candidate_set_hash
    assert m1_results.missing_fields_warning == ("profile.allowed_offer_types",)
    assert m2_results.missing_fields_warning == ("profile.allowed_offer_types",)


def test_cold_start_fallback_order_is_shared_and_never_relaxes_filters(
    tmp_path: Path,
):
    candidates = (
        course_candidate("popular", popularity_score=10),
        course_candidate(
            "less-popular",
            popularity_score=2,
        ),
        course_candidate(
            "pending",
            approval_status="pending_review",
            popularity_score=100,
        ),
    )
    filter_result = filter_candidates(
        candidates,
        complete_filter_profile(
            goals=(),
            current_skills=(),
            target_level=None,
        ),
        {
            "popular": (),
            "less-popular": (),
            "pending": (),
        },
        fallback_limit=2,
        dataset_version_id=VERSION_ID,
    )
    documents = (
        CourseDocument("popular", "Popular course", popularity_score=1),
        CourseDocument("less-popular", "Less popular course", popularity_score=100),
        CourseDocument("pending", "Pending course", popularity_score=1000),
    )
    learner = LearnerProfile("cold-learner")

    m0 = TfidfBaseline(
        documents,
        dataset_version_id=VERSION_ID,
    ).rank(
        learner, top_k=2, candidate_filter_result=filter_result
    )
    m1 = M1SemanticRanker(
        cache_dir=tmp_path / "m1",
        encoder=FakeEncoder(),
    ).rank(
        dataset_version_id=VERSION_ID,
        courses=documents,
        profile=learner,
        top_k=2,
        candidate_filter_result=filter_result,
    )
    m2 = M2HybridRanker(
        M1SemanticRanker(cache_dir=tmp_path / "m2", encoder=FakeEncoder())
    ).rank(
        dataset_version_id=VERSION_ID,
        courses=documents,
        profile=learner,
        target_skills=None,
        current_skill_ids=None,
        target_level=None,
        skill_prerequisites={"popular": (), "less-popular": (), "pending": ()},
        top_k=2,
        candidate_filter_result=filter_result,
    )

    expected = ("popular", "less-popular")
    assert filter_result.fallback_reason == "cold_start"
    assert tuple(item.course.course_id for item in m0) == expected
    assert tuple(item.course_id for item in m1.ranked_courses) == expected
    assert tuple(item.course.course_id for item in m2.ranked_courses) == expected
    assert "pending" not in filter_result.eligible_candidate_ids


class FakeEncoder:
    def encode(
        self,
        sentences: Sequence[str],
        *,
        batch_size: int,
        show_progress_bar: bool,
        convert_to_numpy: bool,
        normalize_embeddings: bool,
    ) -> list[list[float]]:
        return [[1.0, 0.0] for _ in sentences]
