import json
from datetime import datetime, timezone

import pytest

from src.recommendations.candidate_filter import (
    CourseCandidate,
    StudentProfile,
    filter_candidates,
)
from src.recommendations.explanation_builder import (
    RankedItemEvidence,
    build_recommendation_trace,
    ranked_items_from_m0,
    ranked_items_from_m1,
    ranked_items_from_m2,
)
from src.recommendations.m1_semantic import (
    M1RecommendationResult,
    SemanticRankedCourse,
)
from src.recommendations.m2_hybrid import (
    M2RankedCourse,
    M2RecommendationResult,
    M2ScoreComponents,
    WeightedTargetSkill,
)
from src.recommendations.tfidf_baseline import (
    MODEL_VERSION,
    CourseDocument,
    LearnerProfile,
    RankedCourse,
)


VERSION_ID = "dataset-explanations-v1"
REQUEST_ID = "00000000-0000-4000-8000-000000000001"


def test_build_trace_uses_only_versioned_input_evidence():
    candidate = CourseCandidate(
        course_id="sql-course",
        approval_status="approved",
        offer_type="ONLINE",
        price_amount=150000,
        price_currency="VND",
        duration_minutes=600,
        required_hours_per_week=4,
        popularity_score=2,
    )
    filter_profile = StudentProfile(
        goals=("data analyst",),
        current_skills=(),
        target_level="INTERMEDIATE",
        allowed_offer_types=("ONLINE",),
        purchased_course_ids=(),
        enrolled_course_ids=(),
        completed_course_ids=("sql-prerequisite",),
        exclude_course_ids=(),
        exclude_enrolled_or_completed=False,
        max_budget_amount=200000,
        budget_currency="VND",
        available_hours_per_week=5,
    )
    prerequisites = {"sql-course": ("sql-prerequisite",)}
    filter_result = filter_candidates(
        [candidate],
        filter_profile,
        prerequisites,
        dataset_version_id=VERSION_ID,
    )
    course = CourseDocument(
        course_id="sql-course",
        title="SQL for Analysts",
        description="A SQL course.",
        skills=("SQL",),
        direct_skills=("SQL",),
        skill_ids=("sql",),
        level="BEGINNER",
    )
    ranked = RankedItemEvidence(
        course=course,
        rank=1,
        score=91.25,
        score_scale="0-100",
        ranking_method="m2_hybrid",
        dataset_version_id=VERSION_ID,
        model_version="m2-hybrid-v1-test",
        score_components={"S": 1.0, "G": 0.75, "L": 0.5},
    )

    trace = build_recommendation_trace(
        request_id=REQUEST_ID,
        model_name="M2",
        model_version="m2-hybrid-v1-test",
        dataset_version_id=VERSION_ID,
        top_k=3,
        learner_profile=LearnerProfile(
            learner_key="learner-1",
            goals=("data analyst",),
            current_skills=(),
        ),
        ranked_items=(ranked,),
        candidate_filter_result=filter_result,
        target_skills=(WeightedTargetSkill("sql", "SQL", 2.0),),
        current_skill_ids=(),
        target_level="INTERMEDIATE",
        model_config={"weights": {"S": 0.5, "G": 0.35, "L": 0.15}},
        learner_key="learner-1",
        created_at=datetime(2026, 11, 27, tzinfo=timezone.utc),
    )

    item = trace["items"][0]
    explanation = item["explanation"]
    claims = explanation["claims"]
    assert trace["model_version"] == "m2-hybrid-v1-test"
    assert trace["dataset_version_id"] == VERSION_ID
    assert trace["candidate_set_hash"] == filter_result.candidate_set_hash
    assert item["score_components"] == {"S": 1.0, "G": 0.75, "L": 0.5}
    assert [claim["type"] for claim in claims] == [
        "skill_gap",
        "level_fit",
        "prerequisite",
        "price",
        "time",
    ]
    assert explanation["skill_gaps"]["items"] == [
        {
            "skill_id": "sql",
            "label": "SQL",
            "weight": 2.0,
            "source_fields": [
                "profile.target_skills",
                "profile.current_skill_ids",
                "courses.sql-course.skill_ids",
            ],
        }
    ]
    assert explanation["level_fit"]["fit"] == 0.5
    assert explanation["prerequisites"]["completed_required_course_ids"] == [
        "sql-prerequisite"
    ]
    assert explanation["price"]["within_budget"] is True
    assert explanation["time"]["within_available_hours"] is True
    assert explanation["missing_fields_to_confirm"] == []
    assert all(claim["source_fields"] for claim in claims)
    json.dumps(trace, allow_nan=False)


def test_unknown_source_fields_are_reported_without_creating_claims():
    filter_profile = StudentProfile()
    candidate = CourseCandidate(
        course_id="unknown-course",
        approval_status="approved",
        offer_type="ONLINE",
        price_amount=150000,
    )
    filter_result = filter_candidates(
        [candidate],
        filter_profile,
        {"unknown-course": ()},
        dataset_version_id=VERSION_ID,
    )
    course = CourseDocument(
        course_id="unknown-course",
        title="Unknown course",
        skill_ids=None,
        level=None,
    )
    trace = build_recommendation_trace(
        request_id=REQUEST_ID,
        model_name="M1",
        model_version="m1-test",
        dataset_version_id=VERSION_ID,
        top_k=1,
        learner_profile=LearnerProfile("learner-2"),
        ranked_items=(
            RankedItemEvidence(
                course=course,
                rank=1,
                score=None,
                score_scale="0-1",
                ranking_method="popularity_fallback",
                dataset_version_id=VERSION_ID,
                model_version="m1-test",
            ),
        ),
        candidate_filter_result=filter_result,
        target_skills=(WeightedTargetSkill("sql", "SQL", 1.0),),
        current_skill_ids=None,
        target_level=None,
        learner_key="learner-2",
    )

    explanation = trace["items"][0]["explanation"]
    claim_types = {claim["type"] for claim in explanation["claims"]}
    assert "skill_gap" not in claim_types
    assert "level_fit" not in claim_types
    assert "price" not in claim_types
    assert "time" not in claim_types
    assert explanation["prerequisites"]["verified"] is True
    expected_missing = {
        "profile.current_skill_ids",
        "courses.unknown-course.skill_ids",
        "profile.target_level",
        "courses.unknown-course.level",
        "courses.unknown-course.price_currency",
        "courses.unknown-course.duration_minutes",
    }
    assert expected_missing.issubset(
        explanation["missing_fields_to_confirm"]
    ), expected_missing - set(explanation["missing_fields_to_confirm"])


def test_ranker_adapters_keep_original_rank_score_and_model_method():
    course = CourseDocument("course-1", "Course")

    m0 = ranked_items_from_m0(
        (
            RankedCourse(
                course=course,
                rank=1,
                score=0.4,
                ranking_method="tfidf_cosine",
            ),
        ),
        dataset_version_id=VERSION_ID,
    )
    m1 = ranked_items_from_m1(
        M1RecommendationResult(
            dataset_version_id=VERSION_ID,
            model_version="m1-test",
            candidate_set_hash="hash",
            eligible_candidate_ids=("course-1",),
            ranked_courses=(SemanticRankedCourse("course-1", 1, 0.8),),
            fallback_reason=None,
        ),
        (course,),
    )

    assert (m0[0].score, m0[0].ranking_method) == (0.4, "tfidf_cosine")
    assert m0[0].model_version == MODEL_VERSION
    assert (m1[0].score, m1[0].ranking_method) == (0.8, "semantic_cosine")
    with pytest.raises(ValueError, match="missing from course catalog"):
        ranked_items_from_m1(
            M1RecommendationResult(
                dataset_version_id=VERSION_ID,
                model_version="m1-test",
                candidate_set_hash="hash",
                eligible_candidate_ids=("missing",),
                ranked_courses=(SemanticRankedCourse("missing", 1, 0.8),),
                fallback_reason=None,
            ),
            (),
        )


def test_m2_adapter_preserves_effective_weights_for_partial_score_replay():
    item = M2RankedCourse(
        course=CourseDocument("course-1", "Course"),
        rank=1,
        components=M2ScoreComponents(
            semantic=0.8,
            skill_coverage=0.5,
            level_fit=None,
            effective_weights=(0.7, 0.3, 0.0),
            score=71.0,
            completeness="partial",
        ),
    )
    result = M2RecommendationResult(
        dataset_version_id=VERSION_ID,
        model_version="m2-test",
        candidate_set_hash="hash",
        eligible_candidate_ids=("course-1",),
        ranked_courses=(item,),
        skill_roadmap=None,
        roadmap_warning=None,
        semantic_fallback_reason=None,
    )

    evidence = ranked_items_from_m2(result)[0]

    assert evidence.score == 71.0
    assert evidence.score_components == {
        "S": 0.8,
        "G": 0.5,
        "L": None,
    }
    assert evidence.score_metadata == {
        "effective_weights": {"S": 0.7, "G": 0.3, "L": 0.0},
        "completeness": "partial",
    }


def test_trace_rejects_items_outside_shared_candidate_set():
    candidate = CourseCandidate("eligible", "approved", "ONLINE")
    filter_result = filter_candidates(
        [candidate],
        StudentProfile(),
        {"eligible": ()},
        dataset_version_id=VERSION_ID,
    )
    with pytest.raises(ValueError, match="shared eligible candidate set"):
        build_recommendation_trace(
            request_id=REQUEST_ID,
            model_name="M0",
            model_version=MODEL_VERSION,
            dataset_version_id=VERSION_ID,
            top_k=1,
            learner_profile=LearnerProfile("learner-3"),
            ranked_items=(
                RankedItemEvidence(
                    CourseDocument("outside", "Outside"),
                    1,
                    0.2,
                    "cosine_similarity",
                    "tfidf_cosine",
                    VERSION_ID,
                    MODEL_VERSION,
                ),
            ),
            candidate_filter_result=filter_result,
            learner_key="learner-3",
        )


def test_trace_rejects_item_model_version_mismatch():
    candidate = CourseCandidate("eligible", "approved", "ONLINE")
    filter_result = filter_candidates(
        [candidate],
        StudentProfile(),
        {"eligible": ()},
        dataset_version_id=VERSION_ID,
    )
    with pytest.raises(ValueError, match="do not match trace versions"):
        build_recommendation_trace(
            request_id=REQUEST_ID,
            model_name="M0",
            model_version=MODEL_VERSION,
            dataset_version_id=VERSION_ID,
            top_k=1,
            learner_profile=LearnerProfile("learner-4"),
            ranked_items=(
                RankedItemEvidence(
                    CourseDocument("eligible", "Eligible"),
                    1,
                    0.2,
                    "cosine_similarity",
                    "tfidf_cosine",
                    VERSION_ID,
                    "other-model-version",
                ),
            ),
            candidate_filter_result=filter_result,
            learner_key="learner-4",
        )
