from __future__ import annotations

from pathlib import Path
from typing import Sequence

import pytest

from src.recommendations.m1_semantic import M1SemanticRanker
from src.recommendations.m2_hybrid import (
    M2ScoreComponents,
    M2TuningCase,
    M2Weights,
    M2HybridRanker,
    WeightedTargetSkill,
    build_skill_roadmap,
    tune_m2_weights_on_dev,
)
from src.recommendations.tfidf_baseline import CourseDocument, LearnerProfile


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
        return [
            [1.0, 0.0] if "SQL" in sentence else [0.0, 1.0]
            for sentence in sentences
        ]


def build_ranker(tmp_path: Path) -> M2HybridRanker:
    m1 = M1SemanticRanker(cache_dir=tmp_path, encoder=FakeEncoder())
    return M2HybridRanker(m1)


def test_m2_applies_weighted_formula_and_ignores_popularity_when_scored(
    tmp_path: Path,
):
    ranker = build_ranker(tmp_path)
    courses = [
        CourseDocument(
            "sql",
            "SQL for Analysts",
            skills=("SQL",),
            skill_ids=("sql",),
            level="INTERMEDIATE",
            popularity_score=1,
        ),
        CourseDocument(
            "other",
            "Excel for Analysts",
            skills=("Excel",),
            skill_ids=(),
            level="BEGINNER",
            popularity_score=100,
        ),
    ]
    result = ranker.rank(
        dataset_version_id="dataset-v1",
        courses=courses,
        profile=LearnerProfile(
            "learner-1",
            goals=("SQL analyst",),
            candidate_course_ids=("other", "sql"),
        ),
        target_skills=(
            WeightedTargetSkill("sql", "SQL", 3.0),
            WeightedTargetSkill("dashboard", "dashboard reporting", 1.0),
        ),
        current_skill_ids=(),
        target_level="INTERMEDIATE",
        skill_prerequisites={"sql": (), "dashboard": ("sql",)},
    )

    sql_result = result.ranked_courses[0]
    other_result = result.ranked_courses[1]
    assert sql_result.course.course_id == "sql"
    assert sql_result.components.as_dict() == {
        "S": 1.0,
        "G": 0.75,
        "L": 1.0,
    }
    assert sql_result.components.score == 91.25
    assert sql_result.components.completeness == "complete"
    assert other_result.components.as_dict() == {
        "S": 0.5,
        "G": 0.0,
        "L": 0.5,
    }
    assert other_result.components.score == 32.5
    assert result.eligible_candidate_ids == ("other", "sql")
    assert [step.skill_id for step in result.skill_roadmap or ()] == [
        "sql",
        "dashboard",
    ]
    assert result.model_version.startswith("m2-hybrid-v1-S0.5-G0.349")


def test_m2_preserves_unknown_components_and_renormalizes_available_weights(
    tmp_path: Path,
):
    result = build_ranker(tmp_path).rank(
        dataset_version_id="dataset-v1",
        courses=[
            CourseDocument(
                "unknown-metadata",
                "SQL",
                skill_ids=None,
                level=None,
            )
        ],
        profile=LearnerProfile("learner-1", goals=("SQL",)),
        target_skills=(WeightedTargetSkill("sql", "SQL", 1.0),),
        current_skill_ids=(),
        target_level="ADVANCED",
        skill_prerequisites={"sql": ()},
    )

    component = result.ranked_courses[0].components
    assert component.semantic == 1.0
    assert component.skill_coverage is None
    assert component.level_fit is None
    assert component.effective_weights_as_dict() == {"S": 1.0, "G": 0.0, "L": 0.0}
    assert component.score == 100.0
    assert component.completeness == "partial"


def test_empty_skill_gap_is_complete_even_when_course_skill_metadata_is_unknown(
    tmp_path: Path,
):
    result = build_ranker(tmp_path).rank(
        dataset_version_id="dataset-v1",
        courses=[CourseDocument("already-known", "SQL", skill_ids=None)],
        profile=LearnerProfile("learner-1", goals=("SQL",)),
        target_skills=(WeightedTargetSkill("sql", "SQL", 1.0),),
        current_skill_ids=("sql",),
        target_level=None,
        skill_prerequisites=None,
    )

    assert result.ranked_courses[0].components.skill_coverage == 1.0
    assert result.skill_roadmap == ()
    assert result.roadmap_warning is None


def test_all_levels_and_distant_level_fit_are_normalized(tmp_path: Path):
    result = build_ranker(tmp_path).rank(
        dataset_version_id="dataset-v1",
        courses=[
            CourseDocument("all", "SQL", level="ALL_LEVELS"),
            CourseDocument("beginner", "SQL beginner", level="BEGINNER"),
        ],
        profile=LearnerProfile("learner-1", goals=("SQL",)),
        target_skills=(),
        current_skill_ids=(),
        target_level="ADVANCED",
        skill_prerequisites=None,
        top_k=2,
    )

    level_by_course = {
        item.course.course_id: item.components.level_fit
        for item in result.ranked_courses
    }
    assert level_by_course == {"all": 1.0, "beginner": 0.0}


def test_m2_returns_null_score_and_uses_popularity_only_when_all_components_missing(
    tmp_path: Path,
):
    result = build_ranker(tmp_path).rank(
        dataset_version_id="dataset-v1",
        courses=[
            CourseDocument("lower", "Lower", popularity_score=1),
            CourseDocument("higher", "Higher", popularity_score=3),
        ],
        profile=LearnerProfile("learner-1"),
        target_skills=None,
        current_skill_ids=None,
        target_level=None,
        skill_prerequisites=None,
    )

    assert [item.course.course_id for item in result.ranked_courses] == [
        "higher",
        "lower",
    ]
    assert all(item.components.score is None for item in result.ranked_courses)
    assert all(item.components.completeness == "partial" for item in result.ranked_courses)
    assert result.skill_roadmap is None
    assert result.roadmap_warning == "target skills are unknown"
    assert result.semantic_fallback_reason == "cold_start"


def test_roadmap_is_stable_and_omits_completed_prerequisites():
    graph = {
        "sql": (),
        "dashboard": ("sql",),
        "analytics": ("dashboard",),
        "python": (),
    }

    roadmap = build_skill_roadmap(
        ("analytics", "python"),
        ("sql",),
        graph,
    )

    assert [step.skill_id for step in roadmap] == [
        "dashboard",
        "analytics",
        "python",
    ]
    assert roadmap[0].prerequisite_skill_ids == ()
    assert roadmap[1].prerequisite_skill_ids == ("dashboard",)
    assert roadmap[2].is_target is True


@pytest.mark.parametrize(
    ("targets", "graph", "message"),
    [
        (("unknown",), {}, "missing prerequisite mapping"),
        (("unknown",), {"unknown": None}, "prerequisites are unknown"),
        (("a",), {"a": ("b",), "b": ("a",)}, "contains a cycle"),
    ],
)
def test_roadmap_rejects_missing_or_cyclic_prerequisites(targets, graph, message):
    with pytest.raises(ValueError, match=message):
        build_skill_roadmap(targets, (), graph)


def test_weight_tuning_uses_only_dev_and_selects_by_ndcg():
    semantic_first = M2Weights(semantic=1.0, skill_coverage=0.0, level_fit=0.0)
    skill_first = M2Weights(semantic=0.0, skill_coverage=1.0, level_fit=0.0)
    components = {
        "relevant": M2ScoreComponents(1.0, 0.0, 0.0, (1.0, 0.0, 0.0), 100.0, "complete"),
        "irrelevant": M2ScoreComponents(0.0, 1.0, 0.0, (1.0, 0.0, 0.0), 0.0, "complete"),
    }
    case = M2TuningCase(
        profile_key="learner-1",
        filtered_candidate_ids=("relevant", "irrelevant"),
        components_by_course=components,
        relevance_by_course={"relevant": 1, "irrelevant": 0},
    )

    result = tune_m2_weights_on_dev(
        dataset_version_id="dataset-v1",
        cases=(case,),
        weight_candidates=(semantic_first, skill_first),
        split_name="dev",
        top_k=1,
    )

    assert result.selected_weights == semantic_first
    assert result.ndcg_at_k == 1.0
    with pytest.raises(ValueError, match="only be tuned on the dev split"):
        tune_m2_weights_on_dev(
            dataset_version_id="dataset-v1",
            cases=(case,),
            weight_candidates=(semantic_first, skill_first),
            split_name="test",
            top_k=1,
        )
