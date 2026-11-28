"""Hybrid M2 ranking and prerequisite-aware skill roadmaps."""

from __future__ import annotations

import hashlib
import heapq
import math
from dataclasses import dataclass, replace
from typing import Collection, Mapping, Sequence

from src.recommendations.candidate_filter import (
    CandidateFilterResult,
    fallback_ordered_candidate_ids,
    resolve_candidate_course_ids,
    validate_filter_dataset_version,
)
from src.recommendations.evaluation import ModelEvaluationRun, compare_model_runs
from src.recommendations.m1_semantic import M1SemanticRanker
from src.recommendations.tfidf_baseline import (
    CourseDocument,
    LearnerProfile,
    select_candidate_courses,
)


_LEVELS = ("BEGINNER", "INTERMEDIATE", "ADVANCED")


@dataclass(frozen=True)
class M2Weights:
    semantic: float = 0.50
    skill_coverage: float = 0.35
    level_fit: float = 0.15

    def __post_init__(self) -> None:
        values = (self.semantic, self.skill_coverage, self.level_fit)
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in values
        ):
            raise ValueError("M2 weights must be finite numbers")
        if any(value < 0 for value in values):
            raise ValueError("M2 weights must be non-negative")
        if not math.isclose(math.fsum(values), 1.0, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("M2 weights must sum to 1")

    @property
    def version_suffix(self) -> str:
        return (
            f"S{self.semantic:.17g}-G{self.skill_coverage:.17g}"
            f"-L{self.level_fit:.17g}"
        )


DEFAULT_M2_WEIGHTS = M2Weights()


@dataclass(frozen=True)
class WeightedTargetSkill:
    skill_id: str
    label: str
    weight: float

    def __post_init__(self) -> None:
        if not isinstance(self.skill_id, str) or not self.skill_id.strip():
            raise ValueError("skill_id must not be empty")
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError(f"label must not be empty for skill {self.skill_id}")
        if (
            isinstance(self.weight, bool)
            or not isinstance(self.weight, (int, float))
            or not math.isfinite(self.weight)
            or self.weight <= 0
        ):
            raise ValueError("target skill weights must be finite and positive")


@dataclass(frozen=True)
class M2ScoreComponents:
    semantic: float | None
    skill_coverage: float | None
    level_fit: float | None
    effective_weights: tuple[float, float, float]
    score: float | None
    completeness: str

    def as_dict(self) -> dict[str, float | None]:
        return {
            "S": self.semantic,
            "G": self.skill_coverage,
            "L": self.level_fit,
        }

    def effective_weights_as_dict(self) -> dict[str, float]:
        return {
            "S": self.effective_weights[0],
            "G": self.effective_weights[1],
            "L": self.effective_weights[2],
        }


@dataclass(frozen=True)
class RoadmapStep:
    skill_id: str
    prerequisite_skill_ids: tuple[str, ...]
    is_target: bool


@dataclass(frozen=True)
class M2RankedCourse:
    course: CourseDocument
    rank: int
    components: M2ScoreComponents


@dataclass(frozen=True)
class M2RecommendationResult:
    dataset_version_id: str
    model_version: str
    candidate_set_hash: str
    eligible_candidate_ids: tuple[str, ...]
    ranked_courses: tuple[M2RankedCourse, ...]
    skill_roadmap: tuple[RoadmapStep, ...] | None
    roadmap_warning: str | None
    semantic_fallback_reason: str | None
    missing_fields_warning: tuple[str, ...] = ()
    score_scale: str = "0-100"


class M2HybridRanker:
    """Combine M1 semantic fit, weighted skill gaps, and course-level fit."""

    def __init__(
        self,
        semantic_ranker: M1SemanticRanker,
        *,
        weights: M2Weights = DEFAULT_M2_WEIGHTS,
    ) -> None:
        self.semantic_ranker = semantic_ranker
        self.weights = weights
        self.model_version = (
            f"m2-hybrid-v1-{weights.version_suffix};"
            f"m1={semantic_ranker.model_version}"
        )

    def rank(
        self,
        *,
        dataset_version_id: str,
        courses: Sequence[CourseDocument],
        profile: LearnerProfile,
        target_skills: Sequence[WeightedTargetSkill] | None,
        current_skill_ids: Collection[str] | None,
        target_level: str | None,
        skill_prerequisites: Mapping[str, Collection[str] | None] | None,
        top_k: int = 5,
        candidate_filter_result: CandidateFilterResult | None = None,
    ) -> M2RecommendationResult:
        if not isinstance(dataset_version_id, str) or not dataset_version_id.strip():
            raise ValueError("dataset_version_id must not be empty")
        dataset_version_id = dataset_version_id.strip()
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        normalized_targets = _validate_target_skills(target_skills)
        normalized_current = _validate_skill_ids(
            current_skill_ids, field_name="current_skill_ids"
        )
        normalized_level = _normalize_target_level(target_level)
        validate_filter_dataset_version(candidate_filter_result, dataset_version_id)
        filtered_candidate_ids = resolve_candidate_course_ids(
            profile.candidate_course_ids,
            candidate_filter_result,
        )
        candidates = select_candidate_courses(courses, filtered_candidate_ids)
        candidate_ids = tuple(course.course_id for course in candidates)
        candidate_set_hash = hashlib.sha256(
            "\n".join(sorted(candidate_ids)).encode("utf-8")
        ).hexdigest()

        semantic_profile = replace(
            profile,
            candidate_course_ids=candidate_ids,
            goals=profile.goals
            + tuple(skill.label for skill in normalized_targets or ()),
            target_text=" ".join(
                value
                for value in (
                    profile.target_text or "",
                    normalized_level or "",
                )
                if value
            )
            or None,
        )
        semantic_result = self.semantic_ranker.rank(
            dataset_version_id=dataset_version_id,
            courses=courses,
            profile=semantic_profile,
            top_k=max(1, len(candidates)),
        )
        semantic_scores = {
            item.course_id: item.score for item in semantic_result.ranked_courses
        }

        roadmap, roadmap_warning = _build_profile_roadmap(
            targets=normalized_targets,
            current_skill_ids=normalized_current,
            prerequisites=skill_prerequisites,
        )
        components_by_course = {
            course.course_id: _score_components(
                semantic=semantic_scores.get(course.course_id),
                skill_coverage=_gap_coverage(
                    course=course,
                    targets=normalized_targets,
                    current_skill_ids=normalized_current,
                ),
                level_fit=_level_fit(course.level, normalized_level),
                weights=self.weights,
            )
            for course in candidates
        }
        fallback_ids = (
            fallback_ordered_candidate_ids(candidate_filter_result, candidate_ids)
            if candidate_filter_result is not None
            else None
        )
        ranked_courses = _rank_courses(
            candidates,
            components_by_course,
            top_k,
            fallback_candidate_ids=fallback_ids,
        )

        return M2RecommendationResult(
            dataset_version_id=dataset_version_id,
            model_version=self.model_version,
            candidate_set_hash=candidate_set_hash,
            eligible_candidate_ids=semantic_result.eligible_candidate_ids,
            ranked_courses=ranked_courses,
            skill_roadmap=roadmap,
            roadmap_warning=roadmap_warning,
            semantic_fallback_reason=semantic_result.fallback_reason,
            missing_fields_warning=(
                candidate_filter_result.missing_fields_warning
                if candidate_filter_result is not None
                else ()
            ),
        )


def build_skill_roadmap(
    target_skill_ids: Collection[str],
    completed_skill_ids: Collection[str],
    prerequisites: Mapping[str, Collection[str] | None],
) -> tuple[RoadmapStep, ...]:
    """Return a stable topological order for target skills and unmet prerequisites."""
    targets = _validate_skill_ids(target_skill_ids, field_name="target_skill_ids")
    completed = set(
        _validate_skill_ids(completed_skill_ids, field_name="completed_skill_ids")
        or ()
    )
    pending_targets = set(targets or ()) - completed
    if not pending_targets:
        return ()

    dependencies: dict[str, set[str]] = {}
    pending: set[str] = set()
    stack = sorted(pending_targets, reverse=True)
    while stack:
        skill_id = stack.pop()
        if skill_id in pending or skill_id in completed:
            continue
        if skill_id not in prerequisites:
            raise ValueError(f"missing prerequisite mapping for skill {skill_id}")
        raw_prerequisites = prerequisites[skill_id]
        if raw_prerequisites is None:
            raise ValueError(f"prerequisites are unknown for skill {skill_id}")
        if isinstance(raw_prerequisites, str):
            raise ValueError(f"prerequisites for {skill_id} must be a collection of IDs")
        direct = set(
            _validate_skill_ids(
                raw_prerequisites,
                field_name=f"prerequisites[{skill_id}]",
            )
            or ()
        )
        dependencies[skill_id] = direct - completed
        pending.add(skill_id)
        stack.extend(sorted(direct - completed, reverse=True))

    dependents: dict[str, set[str]] = {skill_id: set() for skill_id in pending}
    indegree = {skill_id: len(deps) for skill_id, deps in dependencies.items()}
    for skill_id, required in dependencies.items():
        for prerequisite_id in required:
            if prerequisite_id not in pending:
                raise ValueError(
                    f"missing prerequisite mapping for skill {prerequisite_id}"
                )
            dependents[prerequisite_id].add(skill_id)

    ready = [skill_id for skill_id, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    ordered: list[str] = []
    while ready:
        skill_id = heapq.heappop(ready)
        ordered.append(skill_id)
        for dependent in sorted(dependents[skill_id]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, dependent)

    if len(ordered) != len(pending):
        cyclic = sorted(skill_id for skill_id, degree in indegree.items() if degree > 0)
        raise ValueError("prerequisite graph contains a cycle: " + ", ".join(cyclic))

    target_set = set(targets or ())
    return tuple(
        RoadmapStep(
            skill_id=skill_id,
            prerequisite_skill_ids=tuple(sorted(dependencies[skill_id])),
            is_target=skill_id in target_set,
        )
        for skill_id in ordered
    )


@dataclass(frozen=True)
class M2TuningCase:
    profile_key: str
    filtered_candidate_ids: tuple[str, ...]
    components_by_course: Mapping[str, M2ScoreComponents]
    relevance_by_course: Mapping[str, int]
    popularity_by_course: Mapping[str, float | None] | None = None


@dataclass(frozen=True)
class M2WeightTuningResult:
    selected_weights: M2Weights
    ndcg_at_k: float
    metrics_by_weights: Mapping[str, float]


def tune_m2_weights_on_dev(
    *,
    dataset_version_id: str,
    cases: Sequence[M2TuningCase],
    weight_candidates: Sequence[M2Weights],
    split_name: str,
    top_k: int = 5,
) -> M2WeightTuningResult:
    """Select weights using dev labels only; explicitly reject test-set tuning."""
    if split_name != "dev":
        raise ValueError("M2 weights may only be tuned on the dev split")
    if not isinstance(dataset_version_id, str) or not dataset_version_id.strip():
        raise ValueError("dataset_version_id must not be empty")
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    if not cases or not weight_candidates:
        raise ValueError("dev cases and weight_candidates must not be empty")
    for case in cases:
        if not isinstance(case.profile_key, str) or not case.profile_key.strip():
            raise ValueError("dev profile_key values must be non-empty and unique")
        if any(
            isinstance(grade, bool)
            or not isinstance(grade, int)
            or grade < 0
            for grade in case.relevance_by_course.values()
        ):
            raise ValueError("relevance grades must be non-negative integers")
    if not any(grade > 0 for case in cases for grade in case.relevance_by_course.values()):
        raise ValueError("dev labels must contain at least one relevant course")
    suffixes = [weights.version_suffix for weights in weight_candidates]
    if len(suffixes) != len(set(suffixes)):
        raise ValueError("weight_candidates must be unique")

    profile_keys = [case.profile_key for case in cases]
    if len(profile_keys) != len(set(profile_keys)):
        raise ValueError("dev profile_key values must be non-empty and unique")

    metrics_by_weights: dict[str, float] = {}
    best_weights: M2Weights | None = None
    best_ndcg = -1.0
    for weights in weight_candidates:
        candidate_sets: dict[str, tuple[str, ...]] = {}
        rankings: dict[str, tuple[str, ...]] = {}
        relevance: dict[str, Mapping[str, int]] = {}
        for case in cases:
            candidate_ids = case.filtered_candidate_ids
            if len(candidate_ids) != len(set(candidate_ids)):
                raise ValueError(
                    f"filtered candidate IDs contain duplicates for {case.profile_key}"
                )
            if any(not isinstance(course_id, str) or not course_id.strip() for course_id in candidate_ids):
                raise ValueError(
                    f"filtered candidate IDs must be non-empty strings for {case.profile_key}"
                )
            if set(case.components_by_course) != set(candidate_ids):
                raise ValueError(
                    f"component records must match filtered candidates for {case.profile_key}"
                )
            if set(case.relevance_by_course) - set(candidate_ids):
                raise ValueError(
                    f"relevance labels include filtered-out courses for {case.profile_key}"
                )
            popularity = case.popularity_by_course or {}
            if set(popularity) - set(candidate_ids):
                raise ValueError(
                    f"popularity values include filtered-out courses for {case.profile_key}"
                )
            if any(
                value is not None
                and (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    or value < 0
                )
                for value in popularity.values()
            ):
                raise ValueError("popularity values must be finite and non-negative")

            candidate_sets[case.profile_key] = candidate_ids
            rankings[case.profile_key] = _rank_component_records(
                candidate_ids,
                case.components_by_course,
                popularity,
                weights,
            )
            relevance[case.profile_key] = case.relevance_by_course

        run = ModelEvaluationRun(
            model_name=f"M2-{weights.version_suffix}",
            model_version=f"m2-hybrid-v1-{weights.version_suffix}",
            dataset_version_id=dataset_version_id.strip(),
            filtered_candidate_ids=candidate_sets,
            ranked_course_ids=rankings,
            latency_ms_by_profile={profile_key: 0.0 for profile_key in profile_keys},
        )
        metrics = compare_model_runs(
            relevance_by_profile=relevance,
            runs=(run,),
            top_k=top_k,
        )[run.model_name]
        metrics_by_weights[weights.version_suffix] = metrics.ndcg_at_k
        if metrics.ndcg_at_k > best_ndcg:
            best_weights = weights
            best_ndcg = metrics.ndcg_at_k

    if best_weights is None:
        raise RuntimeError("no M2 weight configuration was evaluated")
    return M2WeightTuningResult(
        selected_weights=best_weights,
        ndcg_at_k=best_ndcg,
        metrics_by_weights=metrics_by_weights,
    )


def _validate_target_skills(
    target_skills: Sequence[WeightedTargetSkill] | None,
) -> tuple[WeightedTargetSkill, ...] | None:
    if target_skills is None:
        return None
    if isinstance(target_skills, (str, bytes, bytearray)):
        raise ValueError("target_skills must be a sequence of WeightedTargetSkill")
    skills = tuple(target_skills)
    if any(not isinstance(skill, WeightedTargetSkill) for skill in skills):
        raise ValueError("target_skills items must be WeightedTargetSkill values")
    skill_ids = [skill.skill_id for skill in skills]
    if len(skill_ids) != len(set(skill_ids)):
        raise ValueError("target skill IDs must be unique")
    return skills


def _validate_skill_ids(
    skill_ids: Collection[str] | None,
    *,
    field_name: str,
) -> tuple[str, ...] | None:
    if skill_ids is None:
        return None
    if isinstance(skill_ids, (str, bytes, bytearray)):
        raise ValueError(f"{field_name} must be a collection of skill IDs or null")
    values = tuple(skill_ids)
    if any(not isinstance(skill_id, str) or not skill_id.strip() for skill_id in values):
        raise ValueError(f"{field_name} must contain non-empty string IDs")
    return tuple(sorted(values))


def _normalize_target_level(target_level: str | None) -> str | None:
    if target_level is None:
        return None
    if not isinstance(target_level, str):
        raise ValueError("target_level must be a string or null")
    normalized = target_level.strip().upper()
    if normalized not in _LEVELS:
        raise ValueError("target_level must be BEGINNER, INTERMEDIATE, ADVANCED, or null")
    return normalized


def _gap_coverage(
    *,
    course: CourseDocument,
    targets: Sequence[WeightedTargetSkill] | None,
    current_skill_ids: Sequence[str] | None,
) -> float | None:
    if targets is None or current_skill_ids is None:
        return None
    current_skills = set(current_skill_ids)
    missing = {
        target.skill_id
        for target in targets
        if target.skill_id not in current_skills
    }
    if not missing:
        return 1.0
    if course.skill_ids is None:
        return None
    course_skill_ids = _validate_skill_ids(
        course.skill_ids, field_name=f"courses[{course.course_id}].skill_ids"
    )
    covered = set(course_skill_ids or ())
    missing_weights = {
        target.skill_id: target.weight for target in targets if target.skill_id in missing
    }
    total_weight = math.fsum(missing_weights.values())
    covered_weight = math.fsum(
        weight for skill_id, weight in missing_weights.items() if skill_id in covered
    )
    return covered_weight / total_weight


def _level_fit(course_level: str | None, target_level: str | None) -> float | None:
    if course_level is None or target_level is None:
        return None
    if not isinstance(course_level, str):
        raise ValueError("course level must be a string or null")
    normalized_course_level = course_level.strip().upper()
    if normalized_course_level == "ALL_LEVELS":
        return 1.0
    if normalized_course_level not in _LEVELS:
        raise ValueError(f"unsupported course level: {course_level}")
    distance = abs(
        _LEVELS.index(normalized_course_level) - _LEVELS.index(target_level)
    )
    return 1.0 - distance / (len(_LEVELS) - 1)


def _score_components(
    *,
    semantic: float | None,
    skill_coverage: float | None,
    level_fit: float | None,
    weights: M2Weights,
) -> M2ScoreComponents:
    values = (semantic, skill_coverage, level_fit)
    configured_weights = (weights.semantic, weights.skill_coverage, weights.level_fit)
    if any(
        value is not None
        and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
            or value > 1
        )
        for value in values
    ):
        raise ValueError("M2 components must be finite values in [0, 1]")
    available_weights = tuple(
        weight if value is not None else 0.0
        for value, weight in zip(values, configured_weights)
    )
    total_available_weight = math.fsum(available_weights)
    if total_available_weight == 0:
        effective_weights = (0.0, 0.0, 0.0)
        score = None
    else:
        effective_weights = tuple(
            weight / total_available_weight for weight in available_weights
        )
        score = round(
            100.0
            * math.fsum(
                effective_weight * value
                for effective_weight, value in zip(effective_weights, values)
                if value is not None
            ),
            8,
        )
    completeness = (
        "complete"
        if all(
            value is not None
            for value, weight in zip(values, configured_weights)
            if weight > 0
        )
        else "partial"
    )
    return M2ScoreComponents(
        semantic=semantic,
        skill_coverage=skill_coverage,
        level_fit=level_fit,
        effective_weights=effective_weights,
        score=score,
        completeness=completeness,
    )


def _rank_courses(
    candidates: Sequence[CourseDocument],
    components_by_course: Mapping[str, M2ScoreComponents],
    top_k: int,
    *,
    fallback_candidate_ids: Sequence[str] | None = None,
) -> tuple[M2RankedCourse, ...]:
    scores = [components_by_course[course.course_id].score for course in candidates]
    if any(score is not None for score in scores):
        ordered = sorted(
            candidates,
            key=lambda course: (
                components_by_course[course.course_id].score is None,
                -(
                    components_by_course[course.course_id].score
                    if components_by_course[course.course_id].score is not None
                    else 0.0
                ),
                course.course_id,
            ),
        )
    else:
        if fallback_candidate_ids is None:
            ordered = sorted(
                candidates,
                key=lambda course: (
                    course.popularity_score is None,
                    -(course.popularity_score or 0.0),
                    course.course_id,
                ),
            )
        else:
            course_index = {course.course_id: course for course in candidates}
            ordered = [
                course_index[course_id]
                for course_id in fallback_candidate_ids
            ]
    return tuple(
        M2RankedCourse(
            course=course,
            rank=index,
            components=components_by_course[course.course_id],
        )
        for index, course in enumerate(ordered[:top_k], start=1)
    )


def _rank_component_records(
    candidate_ids: Sequence[str],
    components_by_course: Mapping[str, M2ScoreComponents],
    popularity_by_course: Mapping[str, float | None],
    weights: M2Weights,
) -> tuple[str, ...]:
    rescored = {
        course_id: _score_components(
            semantic=components_by_course[course_id].semantic,
            skill_coverage=components_by_course[course_id].skill_coverage,
            level_fit=components_by_course[course_id].level_fit,
            weights=weights,
        ).score
        for course_id in candidate_ids
    }
    if any(score is not None for score in rescored.values()):
        return tuple(
            sorted(
                candidate_ids,
                key=lambda course_id: (
                    rescored[course_id] is None,
                    -(rescored[course_id] if rescored[course_id] is not None else 0.0),
                    course_id,
                ),
            )
        )
    return tuple(
        sorted(
            candidate_ids,
            key=lambda course_id: (
                popularity_by_course.get(course_id) is None,
                -(popularity_by_course.get(course_id) or 0.0),
                course_id,
            ),
        )
    )


def _build_profile_roadmap(
    *,
    targets: Sequence[WeightedTargetSkill] | None,
    current_skill_ids: Sequence[str] | None,
    prerequisites: Mapping[str, Collection[str] | None] | None,
) -> tuple[tuple[RoadmapStep, ...] | None, str | None]:
    if targets is None:
        return None, "target skills are unknown"
    if not targets:
        return (), None
    if current_skill_ids is None:
        return None, "current skill IDs are unknown"
    target_ids = tuple(skill.skill_id for skill in targets)
    pending = set(target_ids) - set(current_skill_ids)
    if not pending:
        return (), None
    if prerequisites is None:
        raise ValueError("skill_prerequisites is required for unmet target skills")
    return (
        build_skill_roadmap(target_ids, current_skill_ids, prerequisites),
        None,
    )
