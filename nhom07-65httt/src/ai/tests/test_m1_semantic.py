from __future__ import annotations

from pathlib import Path
from typing import Sequence

import pytest

from src.recommendations.m1_semantic import M1SemanticRanker
from src.recommendations.tfidf_baseline import CourseDocument, LearnerProfile


VERSION_ID = "dataset-test-v1"


class FakeEncoder:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def encode(
        self,
        sentences: Sequence[str],
        *,
        batch_size: int,
        show_progress_bar: bool,
        convert_to_numpy: bool,
        normalize_embeddings: bool,
    ) -> list[list[float]]:
        self.calls.append(list(sentences))
        return [
            [1.0, 0.0] if "SQL" in sentence else [0.0, 1.0]
            for sentence in sentences
        ]


def catalog() -> list[CourseDocument]:
    return [
        CourseDocument("sql-course", "SQL for Data Analysis", skills=("SQL",)),
        CourseDocument("writing-course", "Creative Writing"),
    ]


def learner(
    *,
    goals: tuple[str, ...] = ("SQL analyst",),
    current_skills: tuple[str, ...] = ("Excel",),
    candidate_course_ids: tuple[str, ...] | None = (
        "sql-course",
        "writing-course",
    ),
) -> LearnerProfile:
    return LearnerProfile(
        learner_key="learner-1",
        goals=goals,
        current_skills=current_skills,
        candidate_course_ids=candidate_course_ids,
    )


def test_m1_uses_shared_candidate_ids_and_normalized_cosine_scores(tmp_path: Path):
    encoder = FakeEncoder()
    ranker = M1SemanticRanker(cache_dir=tmp_path, encoder=encoder)

    result = ranker.rank(
        dataset_version_id=VERSION_ID,
        courses=catalog(),
        profile=learner(),
        top_k=5,
    )

    assert [item.course_id for item in result.ranked_courses] == [
        "sql-course",
        "writing-course",
    ]
    assert [item.score for item in result.ranked_courses] == [1.0, 0.5]
    assert result.dataset_version_id == VERSION_ID
    assert result.model_version.endswith("@e8f8c211226b894fcb81acc59f3b34ba3efd5f42")
    assert result.eligible_candidate_ids == ("sql-course", "writing-course")
    assert len(encoder.calls) == 2


def test_course_embeddings_are_cached_per_version_and_catalog(tmp_path: Path):
    encoder = FakeEncoder()
    ranker = M1SemanticRanker(cache_dir=tmp_path, encoder=encoder)

    assert ranker.precompute_catalog(VERSION_ID, catalog()) is False
    assert ranker.precompute_catalog(VERSION_ID, catalog()) is True
    assert len(encoder.calls) == 1

    assert ranker.precompute_catalog("dataset-test-v2", catalog()) is False
    assert len(encoder.calls) == 2


def test_new_ranker_reuses_disk_cache_and_rejects_mutated_published_catalog(
    tmp_path: Path,
):
    first = M1SemanticRanker(cache_dir=tmp_path, encoder=FakeEncoder())
    assert first.precompute_catalog(VERSION_ID, catalog()) is False

    second_encoder = FakeEncoder()
    second = M1SemanticRanker(cache_dir=tmp_path, encoder=second_encoder)
    assert second.precompute_catalog(VERSION_ID, catalog()) is True
    assert second_encoder.calls == []

    changed_courses = [
        CourseDocument("sql-course", "Different SQL course"),
        CourseDocument("writing-course", "Creative Writing"),
    ]
    with pytest.raises(ValueError, match="new dataset version"):
        second.precompute_catalog(VERSION_ID, changed_courses)

    changed_skill_metadata = [
        CourseDocument(
            "sql-course",
            "SQL for Data Analysis",
            skills=("SQL",),
            skill_ids=("skill-sql",),
        ),
        CourseDocument("writing-course", "Creative Writing"),
    ]
    with pytest.raises(ValueError, match="new dataset version"):
        second.precompute_catalog(VERSION_ID, changed_skill_metadata)


def test_cold_start_uses_candidate_popularity_without_loading_model(tmp_path: Path):
    encoder = FakeEncoder()
    ranker = M1SemanticRanker(cache_dir=tmp_path, encoder=encoder)
    courses = [
        CourseDocument("lower", "Lower popularity", popularity_score=1),
        CourseDocument("higher", "Higher popularity", popularity_score=5),
    ]

    result = ranker.rank(
        dataset_version_id=VERSION_ID,
        courses=courses,
        profile=learner(
            goals=(),
            current_skills=(),
            candidate_course_ids=("lower", "higher"),
        ),
        top_k=1,
    )

    assert [item.course_id for item in result.ranked_courses] == ["higher"]
    assert result.ranked_courses[0].score is None
    assert result.fallback_reason == "cold_start"
    assert encoder.calls == []


def test_rank_rejects_unknown_candidates_and_invalid_requests(tmp_path: Path):
    ranker = M1SemanticRanker(cache_dir=tmp_path, encoder=FakeEncoder())

    with pytest.raises(ValueError, match="unknown courses"):
        ranker.rank(
            dataset_version_id=VERSION_ID,
            courses=catalog(),
            profile=learner(candidate_course_ids=("missing",)),
        )
    with pytest.raises(ValueError, match="at least 1"):
        ranker.rank(
            dataset_version_id=VERSION_ID,
            courses=catalog(),
            profile=learner(),
            top_k=0,
        )
    with pytest.raises(ValueError, match="non-empty string"):
        ranker.rank(
            dataset_version_id=" ",
            courses=catalog(),
            profile=learner(),
        )
