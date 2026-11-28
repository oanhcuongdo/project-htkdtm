"""Compare M0/M1/M2 on a learner-held-out, manually judged dataset."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import time
from typing import Any, Callable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from src.recommendations.candidate_filter import (
    CandidateFilterResult,
    CourseCandidate,
    StudentProfile as FilterStudentProfile,
    count_prerequisite_violations,
    filter_candidates,
    resolve_candidate_course_ids,
)
from src.recommendations.evaluate_tfidf import (
    _filter_profile,
    _parse_candidates,
    _parse_courses,
    _parse_course_prerequisites,
    _parse_profiles,
)
from src.recommendations.evaluation import (
    ModelEvaluationRun,
    RankingMetrics,
    benchmark_latency,
    compare_model_runs,
)
from src.recommendations.m1_semantic import M1SemanticRanker
from src.recommendations.m2_hybrid import (
    M2HybridRanker,
    M2TuningCase,
    M2Weights,
    WeightedTargetSkill,
    tune_m2_weights_on_dev,
)
from src.recommendations.tfidf_baseline import (
    MODEL_VERSION,
    VECTORIZER_CONFIG,
    CourseDocument,
    LearnerProfile,
    TfidfBaseline,
)


@dataclass(frozen=True)
class EvaluationProfile:
    learner_key: str
    split: str
    learner_profile: LearnerProfile
    filter_profile: FilterStudentProfile
    relevance_by_course: Mapping[str, int]
    target_skills: tuple[WeightedTargetSkill, ...] | None
    current_skill_ids: tuple[str, ...] | None
    skill_prerequisites: Mapping[str, tuple[str, ...] | None] | None


@dataclass(frozen=True)
class ModelSpec:
    name: str
    model_version: str
    rank: Callable[
        [EvaluationProfile, CandidateFilterResult, int], tuple[str, ...]
    ]


@dataclass(frozen=True)
class PreparedProfile:
    profile: EvaluationProfile
    filter_result: CandidateFilterResult
    candidate_ids: tuple[str, ...]


def _read_json(path: Path) -> object:
    with path.open(encoding="utf-8-sig") as file:
        return json.load(file)


def _read_course_data(
    path: Path,
) -> tuple[
    tuple[CourseDocument, ...],
    tuple[CourseCandidate, ...],
    dict[str, tuple[str, ...] | None],
]:
    raw = _read_json(path)
    if isinstance(raw, dict):
        records = raw.get("courses")
    else:
        records = raw
    if not isinstance(records, list) or not records:
        raise ValueError("courses input must contain a non-empty JSON course array")
    if any(not isinstance(record, dict) for record in records):
        raise ValueError("every course record must be a JSON object")
    for index, record in enumerate(records):
        for field in ("approval_status", "prerequisite_course_ids"):
            if field not in record:
                raise ValueError(
                    f"courses[{index}].{field} is required; do not infer it from "
                    "quality_status or free-text prerequisites"
                )
    courses = _parse_courses(records)
    candidates = _parse_candidates(records)
    prerequisites = _parse_course_prerequisites(records)
    if len(courses) != len({course.course_id for course in courses}):
        raise ValueError("course_id values must be unique")
    return courses, candidates, prerequisites


def _parse_target_skills(
    record: Mapping[str, object],
    source: str,
) -> tuple[WeightedTargetSkill, ...] | None:
    raw = record.get("target_skills")
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise ValueError(f"{source}.target_skills must be an array or null")
    skills: list[WeightedTargetSkill] = []
    for index, item in enumerate(raw):
        item_source = f"{source}.target_skills[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{item_source} must be an object")
        skill_id = item.get("skill_id")
        label = item.get("label")
        weight = item.get("weight")
        if not isinstance(skill_id, str) or not skill_id.strip():
            raise ValueError(f"{item_source}.skill_id must be a non-empty string")
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"{item_source}.label must be a non-empty string")
        if (
            isinstance(weight, bool)
            or not isinstance(weight, (int, float))
            or not math.isfinite(weight)
            or weight <= 0
        ):
            raise ValueError(f"{item_source}.weight must be finite and positive")
        skills.append(WeightedTargetSkill(skill_id, label, float(weight)))
    if len({skill.skill_id for skill in skills}) != len(skills):
        raise ValueError(f"{source}.target_skills must have unique skill_id values")
    return tuple(skills)


def _parse_optional_ids(
    record: Mapping[str, object],
    field: str,
    source: str,
) -> tuple[str, ...] | None:
    raw = record.get(field)
    if raw is None:
        return None
    if not isinstance(raw, list) or any(
        not isinstance(value, str) or not value.strip() for value in raw
    ):
        raise ValueError(f"{source}.{field} must be an array of non-empty strings or null")
    if len(raw) != len(set(raw)):
        raise ValueError(f"{source}.{field} must not contain duplicates")
    return tuple(raw)


def _parse_skill_prerequisites(
    record: Mapping[str, object],
    source: str,
) -> Mapping[str, tuple[str, ...] | None] | None:
    raw = record.get("skill_prerequisites")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError(f"{source}.skill_prerequisites must be an object or null")
    prerequisites: dict[str, tuple[str, ...] | None] = {}
    for skill_id, raw_ids in raw.items():
        if not isinstance(skill_id, str) or not skill_id.strip():
            raise ValueError(f"{source}.skill_prerequisites keys must be non-empty strings")
        if raw_ids is None:
            prerequisites[skill_id] = None
        elif isinstance(raw_ids, list) and all(
            isinstance(value, str) and value.strip() for value in raw_ids
        ):
            if len(raw_ids) != len(set(raw_ids)):
                raise ValueError(
                    f"{source}.skill_prerequisites[{skill_id}] contains duplicate IDs"
                )
            prerequisites[skill_id] = tuple(raw_ids)
        else:
            raise ValueError(
                f"{source}.skill_prerequisites[{skill_id}] must be an array or null"
            )
    return prerequisites


def load_ground_truth(
    path: Path,
    *,
    dataset_version_id: str,
    course_ids: set[str],
) -> tuple[EvaluationProfile, ...]:
    raw = _read_json(path)
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise ValueError("ground truth must be an object with schema_version=1")
    if raw.get("split_strategy") != "group_by_learner":
        raise ValueError("ground truth split_strategy must be group_by_learner")
    declared_version = raw.get("dataset_version_id")
    if declared_version is not None and declared_version != dataset_version_id:
        raise ValueError("ground truth dataset_version_id does not match the catalog")
    records = raw.get("profiles")
    if not isinstance(records, list) or not records:
        raise ValueError("ground truth profiles must be a non-empty array")

    profiles: list[EvaluationProfile] = []
    learner_keys: set[str] = set()
    for index, record in enumerate(records):
        source = f"profiles[{index}]"
        if not isinstance(record, dict):
            raise ValueError(f"{source} must be an object")
        split = record.get("split")
        if split not in ("dev", "test"):
            raise ValueError(f"{source}.split must be dev or test")
        learner_profile = _parse_profiles((record,))[0]
        if learner_profile.learner_key in learner_keys:
            raise ValueError(
                "each learner_key must occur in only one split and profile"
            )
        learner_keys.add(learner_profile.learner_key)
        filter_profile = _filter_profile(record, source)

        raw_relevance = record.get("relevance")
        if not isinstance(raw_relevance, dict):
            raise ValueError(f"{source}.relevance must be an object of judged course grades")
        relevance: dict[str, int] = {}
        for course_id, grade in raw_relevance.items():
            if course_id not in course_ids:
                raise ValueError(f"{source}.relevance references unknown course {course_id}")
            if isinstance(grade, bool) or not isinstance(grade, int) or grade not in (0, 1, 2):
                raise ValueError(f"{source}.relevance grades must be 0, 1, or 2")
            relevance[course_id] = grade

        target_skills = _parse_target_skills(record, source)
        current_skill_ids = _parse_optional_ids(
            record, "current_skill_ids", source
        )
        skill_prerequisites = _parse_skill_prerequisites(record, source)
        if target_skills and current_skill_ids is None:
            raise ValueError(
                f"{source}.current_skill_ids is required when target_skills are supplied"
            )
        if target_skills and current_skill_ids is not None:
            pending_skill_ids = {
                skill.skill_id for skill in target_skills
            } - set(current_skill_ids)
            if pending_skill_ids and skill_prerequisites is None:
                raise ValueError(
                    f"{source}.skill_prerequisites is required for unmet target skills"
                )
        profiles.append(
            EvaluationProfile(
                learner_key=learner_profile.learner_key,
                split=split,
                learner_profile=learner_profile,
                filter_profile=filter_profile,
                relevance_by_course=relevance,
                target_skills=target_skills,
                current_skill_ids=current_skill_ids,
                skill_prerequisites=skill_prerequisites,
            )
        )
    splits = {profile.split for profile in profiles}
    if splits != {"dev", "test"}:
        raise ValueError("ground truth must contain separate dev and test learners")
    return tuple(profiles)


def _make_model_specs(
    *,
    baseline: TfidfBaseline,
    semantic: M1SemanticRanker,
    courses: Sequence[CourseDocument],
    dataset_version_id: str,
    top_k: int,
    weights: M2Weights,
) -> tuple[ModelSpec, ...]:
    hybrid = M2HybridRanker(semantic, weights=weights)
    no_g_weights = _ablate_weights(weights, "G")
    no_l_weights = _ablate_weights(weights, "L")
    no_g = M2HybridRanker(semantic, weights=no_g_weights)
    no_l = M2HybridRanker(semantic, weights=no_l_weights)

    def rank_m0(
        case: EvaluationProfile,
        filtered: CandidateFilterResult,
        limit: int,
    ) -> tuple[str, ...]:
        candidate_ids = resolve_candidate_course_ids(
            case.learner_profile.candidate_course_ids,
            filtered,
        )
        profile = replace(
            case.learner_profile,
            candidate_course_ids=candidate_ids,
        )
        return tuple(
            item.course.course_id
            for item in baseline.rank(
                profile,
                top_k=limit,
                candidate_filter_result=filtered,
            )
        )

    def rank_m1(
        case: EvaluationProfile,
        filtered: CandidateFilterResult,
        limit: int,
    ) -> tuple[str, ...]:
        candidate_ids = resolve_candidate_course_ids(
            case.learner_profile.candidate_course_ids,
            filtered,
        )
        profile = replace(
            case.learner_profile,
            candidate_course_ids=candidate_ids,
        )
        result = semantic.rank(
            dataset_version_id=dataset_version_id,
            courses=courses,
            profile=profile,
            top_k=limit,
            candidate_filter_result=filtered,
        )
        return tuple(item.course_id for item in result.ranked_courses)

    def hybrid_ranker(ranker: M2HybridRanker) -> Callable[
        [EvaluationProfile, CandidateFilterResult, int], tuple[str, ...]
    ]:
        def rank(
            case: EvaluationProfile,
            filtered: CandidateFilterResult,
            limit: int,
        ) -> tuple[str, ...]:
            candidate_ids = resolve_candidate_course_ids(
                case.learner_profile.candidate_course_ids,
                filtered,
            )
            profile = replace(
                case.learner_profile,
                candidate_course_ids=candidate_ids,
            )
            result = ranker.rank(
                dataset_version_id=dataset_version_id,
                courses=courses,
                profile=profile,
                target_skills=case.target_skills,
                current_skill_ids=case.current_skill_ids,
                target_level=case.filter_profile.target_level,
                skill_prerequisites=case.skill_prerequisites,
                top_k=limit,
                candidate_filter_result=filtered,
            )
            return tuple(item.course.course_id for item in result.ranked_courses)

        return rank

    return (
        ModelSpec("M0", MODEL_VERSION, rank_m0),
        ModelSpec("M1", semantic.model_version, rank_m1),
        ModelSpec("M2", hybrid.model_version, hybrid_ranker(hybrid)),
        ModelSpec("M2-no-G", no_g.model_version, hybrid_ranker(no_g)),
        ModelSpec("M2-no-L", no_l.model_version, hybrid_ranker(no_l)),
    )


def _ablate_weights(weights: M2Weights, component: str) -> M2Weights:
    values = {
        "S": weights.semantic,
        "G": weights.skill_coverage,
        "L": weights.level_fit,
    }
    if component not in values:
        raise ValueError(f"unsupported M2 component ablation: {component}")
    values[component] = 0.0
    total = math.fsum(values.values())
    if total <= 0:
        raise ValueError(f"cannot remove {component}; no M2 weights remain")
    return M2Weights(
        semantic=values["S"] / total,
        skill_coverage=values["G"] / total,
        level_fit=values["L"] / total,
    )


def _prepare_profile(
    profile: EvaluationProfile,
    *,
    course_candidates: Sequence[CourseCandidate],
    prerequisites: Mapping[str, Sequence[str] | None],
    dataset_version_id: str,
    top_k: int,
) -> PreparedProfile:
    filtered = filter_candidates(
        course_candidates,
        profile.filter_profile,
        prerequisites,
        dataset_version_id=dataset_version_id,
        fallback_limit=top_k,
    )
    candidate_ids = resolve_candidate_course_ids(
        profile.learner_profile.candidate_course_ids,
        filtered,
    )
    return PreparedProfile(
        profile=profile,
        filter_result=filtered,
        candidate_ids=tuple(candidate_ids or ()),
    )


def _tune_weights(
    *,
    dev_profiles: Sequence[EvaluationProfile],
    course_candidates: Sequence[CourseCandidate],
    prerequisites: Mapping[str, Sequence[str] | None],
    dataset_version_id: str,
    top_k: int,
    courses: Sequence[CourseDocument],
    semantic: M1SemanticRanker,
) -> dict[str, Any]:
    base = M2HybridRanker(semantic)
    cases: list[M2TuningCase] = []
    for profile in dev_profiles:
        prepared = _prepare_profile(
            profile,
            course_candidates=course_candidates,
            prerequisites=prerequisites,
            dataset_version_id=dataset_version_id,
            top_k=top_k,
        )
        all_candidates_k = max(1, len(prepared.candidate_ids))
        candidate_profile = replace(
            profile.learner_profile,
            candidate_course_ids=prepared.candidate_ids,
        )
        result = base.rank(
            dataset_version_id=dataset_version_id,
            courses=courses,
            profile=candidate_profile,
            target_skills=profile.target_skills,
            current_skill_ids=profile.current_skill_ids,
            target_level=profile.filter_profile.target_level,
            skill_prerequisites=profile.skill_prerequisites,
            top_k=all_candidates_k,
            candidate_filter_result=prepared.filter_result,
        )
        components = {
            item.course.course_id: item.components for item in result.ranked_courses
        }
        cases.append(
            M2TuningCase(
                profile_key=profile.learner_key,
                filtered_candidate_ids=prepared.candidate_ids,
                components_by_course=components,
                relevance_by_course={
                    course_id: grade
                    for course_id, grade in profile.relevance_by_course.items()
                    if course_id in set(prepared.candidate_ids)
                },
                popularity_by_course={
                    candidate.course_id: candidate.popularity_score
                    for candidate in course_candidates
                    if candidate.course_id in set(prepared.candidate_ids)
                },
            )
        )
    grid = (
        M2Weights(0.50, 0.35, 0.15),
        M2Weights(0.60, 0.25, 0.15),
        M2Weights(0.45, 0.40, 0.15),
        M2Weights(0.50, 0.25, 0.25),
        M2Weights(0.40, 0.40, 0.20),
        M2Weights(0.55, 0.35, 0.10),
        M2Weights(0.40, 0.45, 0.15),
        M2Weights(0.60, 0.30, 0.10),
    )
    result = tune_m2_weights_on_dev(
        dataset_version_id=dataset_version_id,
        cases=cases,
        weight_candidates=grid,
        split_name="dev",
        top_k=top_k,
    )
    return {
        "split": "dev",
        "selected_weights": {
            "S": result.selected_weights.semantic,
            "G": result.selected_weights.skill_coverage,
            "L": result.selected_weights.level_fit,
        },
        "selected_ndcg_at_k": result.ndcg_at_k,
        "ndcg_by_candidate_weights": dict(result.metrics_by_weights),
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _metrics_record(
    name: str,
    version: str,
    metrics: RankingMetrics,
    *,
    profile_count: int,
    labeled_pair_count: int,
    course_count: int,
    relative_ndcg_gain: float | None,
    goals: Mapping[str, bool | None],
) -> dict[str, Any]:
    return {
        "model_name": name,
        "model_version": version,
        "profile_count": profile_count,
        "labeled_pair_count": labeled_pair_count,
        "course_count": course_count,
        "ndcg_at_5": metrics.ndcg_at_k,
        "precision_at_5": metrics.precision_at_k,
        "prerequisite_violations": metrics.prerequisite_violations,
        "profiles_under_5_results": metrics.profiles_under_top_k,
        "p50_latency_ms": metrics.p50_latency_ms,
        "p95_latency_ms": metrics.p95_latency_ms,
        "relative_ndcg_gain_vs_m0": relative_ndcg_gain,
        "goal_status": dict(goals),
    }


def run_evaluation(
    *,
    courses_path: Path,
    ground_truth_path: Path,
    output_dir: Path,
    dataset_version_id: str,
    top_k: int = 5,
    warmup_runs: int = 10,
    measured_runs: int = 100,
    min_course_count: int = 250,
    min_labeled_pairs: int = 300,
    tune_m2_on_dev: bool = False,
    semantic_ranker: M1SemanticRanker | None = None,
) -> dict[str, Any]:
    """Run a repeatable comparison and write JSON/Markdown report files."""
    if top_k != 5:
        raise ValueError("the acceptance evaluation is defined at K=5")
    if warmup_runs < 1:
        raise ValueError("at least one warmup call is required")
    if measured_runs < 100:
        raise ValueError("at least 100 measured calls are required for P95")
    if min_course_count < 1 or min_labeled_pairs < 0:
        raise ValueError("minimum input counts are invalid")
    if not dataset_version_id.strip():
        raise ValueError("dataset_version_id must not be empty")

    courses, course_candidates, course_prerequisites = _read_course_data(courses_path)
    if len(courses) < min_course_count:
        raise ValueError(
            f"catalog has {len(courses)} courses; at least {min_course_count} are "
            "required for the approximately-300-course benchmark"
        )
    profiles = load_ground_truth(
        ground_truth_path,
        dataset_version_id=dataset_version_id,
        course_ids={course.course_id for course in courses},
    )
    dev_profiles = tuple(profile for profile in profiles if profile.split == "dev")
    test_profiles = tuple(profile for profile in profiles if profile.split == "test")
    labeled_pair_count = sum(len(profile.relevance_by_course) for profile in profiles)
    test_labeled_pair_count = sum(
        len(profile.relevance_by_course) for profile in test_profiles
    )
    if labeled_pair_count < min_labeled_pairs:
        raise ValueError(
            f"ground truth has {labeled_pair_count} labeled pairs; "
            f"at least {min_labeled_pairs} are required"
        )

    protected_paths = {courses_path.resolve(), ground_truth_path.resolve()}
    report_json_path = output_dir / "model-evaluation-report.json"
    report_markdown_path = output_dir / "model-evaluation-report.md"
    if report_json_path.resolve() in protected_paths or report_markdown_path.resolve() in protected_paths:
        raise ValueError("report outputs must not overwrite evaluation inputs")

    semantic = semantic_ranker or M1SemanticRanker()
    cache_reused = semantic.precompute_catalog(dataset_version_id, courses)
    tuned: dict[str, Any] | None = None
    weights = M2Weights()
    if tune_m2_on_dev:
        tuned = _tune_weights(
            dev_profiles=dev_profiles,
            course_candidates=course_candidates,
            prerequisites=course_prerequisites,
            dataset_version_id=dataset_version_id,
            top_k=top_k,
            courses=courses,
            semantic=semantic,
        )
        selected = tuned["selected_weights"]
        weights = M2Weights(
            semantic=selected["S"],
            skill_coverage=selected["G"],
            level_fit=selected["L"],
        )

    baseline = TfidfBaseline(courses, dataset_version_id=dataset_version_id)
    model_specs = _make_model_specs(
        baseline=baseline,
        semantic=semantic,
        courses=courses,
        dataset_version_id=dataset_version_id,
        top_k=top_k,
        weights=weights,
    )
    prepared_test = tuple(
        _prepare_profile(
            profile,
            course_candidates=course_candidates,
            prerequisites=course_prerequisites,
            dataset_version_id=dataset_version_id,
            top_k=top_k,
        )
        for profile in test_profiles
    )
    if not prepared_test:
        raise ValueError("at least one held-out test learner is required")

    rankings_by_model: dict[str, dict[str, tuple[str, ...]]] = {
        model.name: {} for model in model_specs
    }
    latencies_by_model: dict[str, dict[str, float]] = {
        model.name: {} for model in model_specs
    }
    violations_by_model: dict[str, dict[str, int]] = {
        model.name: {} for model in model_specs
    }
    candidate_sets = {
        item.profile.learner_key: item.candidate_ids for item in prepared_test
    }
    relevance = {
        item.profile.learner_key: item.profile.relevance_by_course
        for item in prepared_test
    }
    for prepared in prepared_test:
        for model in model_specs:
            started = time.perf_counter()
            ranked_ids = model.rank(prepared.profile, prepared.filter_result, top_k)
            latencies_by_model[model.name][prepared.profile.learner_key] = (
                time.perf_counter() - started
            ) * 1000
            rankings_by_model[model.name][prepared.profile.learner_key] = ranked_ids
            violations_by_model[model.name][prepared.profile.learner_key] = (
                count_prerequisite_violations(
                    ranked_ids,
                    prepared.profile.filter_profile.completed_course_ids,
                    course_prerequisites,
                )
            )

    benchmark_profile = max(
        prepared_test,
        key=lambda item: (len(item.candidate_ids), item.profile.learner_key),
    )
    if not benchmark_profile.candidate_ids:
        raise ValueError("no test learner has eligible courses for a latency benchmark")

    runs: list[ModelEvaluationRun] = []
    benchmark_samples: dict[str, tuple[float, ...]] = {}
    for model in model_specs:
        def rank_once(
            selected_model: ModelSpec = model,
            selected_profile: EvaluationProfile = benchmark_profile.profile,
        ) -> object:
            filtered = filter_candidates(
                course_candidates,
                selected_profile.filter_profile,
                course_prerequisites,
                dataset_version_id=dataset_version_id,
                fallback_limit=top_k,
            )
            selected_model.rank(selected_profile, filtered, top_k)
            return None

        samples = benchmark_latency(
            rank_once,
            warmup_runs=warmup_runs,
            measured_runs=measured_runs,
        )
        benchmark_samples[model.name] = samples
        runs.append(
            ModelEvaluationRun(
                model_name=model.name,
                model_version=model.model_version,
                dataset_version_id=dataset_version_id,
                filtered_candidate_ids=candidate_sets,
                ranked_course_ids=rankings_by_model[model.name],
                latency_ms_by_profile=latencies_by_model[model.name],
                latency_samples_ms=samples,
                prerequisite_violations_by_profile=violations_by_model[model.name],
            )
        )

    metrics = compare_model_runs(
        relevance_by_profile=relevance,
        runs=runs,
        top_k=top_k,
    )
    by_name = {model.name: model for model in model_specs}
    baseline_ndcg = metrics["M0"].ndcg_at_k
    metric_rows: list[dict[str, Any]] = []
    for name in rankings_by_model:
        item = metrics[name]
        relative_gain = (
            (item.ndcg_at_k - baseline_ndcg) / baseline_ndcg
            if baseline_ndcg > 0
            else None
        )
        metric_rows.append(
            _metrics_record(
                name,
                by_name[name].model_version,
                item,
                profile_count=len(test_profiles),
                labeled_pair_count=test_labeled_pair_count,
                course_count=len(courses),
                relative_ndcg_gain=relative_gain,
                goals={
                    "precision_at_5_ge_0_70": (
                        item.precision_at_k >= 0.70 if name == "M2" else None
                    ),
                    "ndcg_at_5_ge_m0_plus_10_percent": (
                        item.ndcg_at_k >= baseline_ndcg * 1.10
                        if name == "M2" and baseline_ndcg > 0
                        else None
                    ),
                    "p95_latency_le_3000_ms": (
                        item.p95_latency_ms <= 3000 if name in ("M0", "M1", "M2") else None
                    ),
                    "zero_prerequisite_violations": (
                        item.prerequisite_violations == 0
                    ),
                },
            )
        )

    positive_labels_filtered_out = sum(
        grade > 0 and course_id not in set(candidate_sets[learner_key])
        for learner_key, grades in relevance.items()
        for course_id, grade in grades.items()
    )
    total_candidate_pairs = sum(len(candidate_ids) for candidate_ids in candidate_sets.values())
    judged_eligible_pairs = sum(
        course_id in set(candidate_sets[learner_key])
        for learner_key, grades in relevance.items()
        for course_id in grades
    )
    no_g_weights = _ablate_weights(weights, "G")
    no_l_weights = _ablate_weights(weights, "L")
    report: dict[str, Any] = {
        "schema_version": 1,
        "evaluation_batch_id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_version_id": dataset_version_id,
        "evaluation_split": "test",
        "split_strategy": "group_by_learner",
        "top_k": top_k,
        "catalog_course_count": len(courses),
        "approved_course_count": sum(
            candidate.approval_status is not None
            and candidate.approval_status.strip().lower() == "approved"
            for candidate in course_candidates
        ),
        "dev_profile_count": len(dev_profiles),
        "test_profile_count": len(test_profiles),
        "labeled_pair_count_all_splits": labeled_pair_count,
        "labeled_pair_count_test": test_labeled_pair_count,
        "eligible_labeled_pair_count_test": judged_eligible_pairs,
        "test_candidate_pair_count": total_candidate_pairs,
        "test_judgment_coverage": (
            judged_eligible_pairs / total_candidate_pairs
            if total_candidate_pairs
            else 0.0
        ),
        "positive_labels_excluded_by_hard_filters": positive_labels_filtered_out,
        "unjudged_pairs_treated_as_nonrelevant": True,
        "course_catalog_sha256": _sha256_file(courses_path),
        "ground_truth_sha256": _sha256_file(ground_truth_path),
        "python_version": platform.python_version(),
        "embedding_cache_reused": cache_reused,
        "latency_scope": (
            "in-process shared hard filter plus ranker call; excludes HTTP and "
            "database persistence because no online recommendation orchestrator "
            "is currently connected"
        ),
        "model_config": {
            "M0": {
                "model_version": MODEL_VERSION,
                "vectorizer": VECTORIZER_CONFIG,
            },
            "M1": {
                "model_version": semantic.model_version,
                "model_name": semantic.model_name,
                "model_revision": semantic.model_revision,
                "batch_size": semantic.batch_size,
            },
            "M2": {
                "selected_weights": {
                    "S": weights.semantic,
                    "G": weights.skill_coverage,
                    "L": weights.level_fit,
                },
                "no_G_weights": {
                    "S": no_g_weights.semantic,
                    "G": no_g_weights.skill_coverage,
                    "L": no_g_weights.level_fit,
                },
                "no_L_weights": {
                    "S": no_l_weights.semantic,
                    "G": no_l_weights.skill_coverage,
                    "L": no_l_weights.level_fit,
                },
            },
        },
        "latency_benchmark": {
            "warmup_runs_per_model": warmup_runs,
            "measured_runs_per_model": measured_runs,
            "benchmark_learner_key": benchmark_profile.profile.learner_key,
            "benchmark_eligible_course_count": len(benchmark_profile.candidate_ids),
            "benchmark_course_catalog_count": len(courses),
            "p95_uses_nearest_rank": True,
        },
        "m2_weight_tuning": tuned
        or {
            "split": None,
            "selected_weights": {
                "S": weights.semantic,
                "G": weights.skill_coverage,
                "L": weights.level_fit,
            },
            "note": "canonical weights used; no dev tuning requested",
        },
        "metrics": metric_rows,
        "per_model_latency_samples_ms": {
            name: list(samples) for name, samples in benchmark_samples.items()
        },
        "goal_assessment": _goal_assessment(metrics),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    report_json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    report_markdown_path.write_text(_render_report(report), encoding="utf-8")
    return report


def _goal_assessment(metrics: Mapping[str, RankingMetrics]) -> dict[str, Any]:
    baseline = metrics["M0"].ndcg_at_k
    hybrid = metrics["M2"]
    return {
        "precision_at_5_ge_0_70": {
            "value": hybrid.precision_at_k,
            "target": 0.70,
            "passed": hybrid.precision_at_k >= 0.70,
        },
        "ndcg_at_5_ge_m0_plus_10_percent": {
            "m0": baseline,
            "m2": hybrid.ndcg_at_k,
            "relative_gain": (
                (hybrid.ndcg_at_k - baseline) / baseline if baseline > 0 else None
            ),
            "target_relative_gain": 0.10,
            "passed": (
                hybrid.ndcg_at_k >= baseline * 1.10 if baseline > 0 else None
            ),
            "status": "not_computable_baseline_ndcg_zero" if baseline == 0 else "evaluated",
        },
        "p95_latency_le_3000_ms": {
            name: {
                "value_ms": metrics[name].p95_latency_ms,
                "target_ms": 3000,
                "passed": metrics[name].p95_latency_ms <= 3000,
            }
            for name in ("M0", "M1", "M2")
        },
        "zero_prerequisite_violations": {
            name: metrics[name].prerequisite_violations
            for name in ("M0", "M1", "M2")
        },
    }


def _render_report(report: Mapping[str, Any]) -> str:
    lines = [
        "# Recommender offline evaluation",
        "",
        f"- Evaluation batch: `{report['evaluation_batch_id']}`",
        f"- Dataset version: `{report['dataset_version_id']}`",
        f"- Split: `{report['evaluation_split']}` (grouped by learner)",
        f"- Courses: {report['catalog_course_count']} total, "
        f"{report['approved_course_count']} approved",
        f"- Test learners: {report['test_profile_count']}",
        f"- Test judged pairs: {report['labeled_pair_count_test']}",
        f"- Test judgment coverage: {report['test_judgment_coverage']:.2%}",
        f"- Positive labels excluded by hard filters: "
        f"{report['positive_labels_excluded_by_hard_filters']}",
        "- Unjudged course pairs are treated as non-relevant; interpret metrics "
        "alongside judgment coverage.",
        "",
        "## Results",
        "",
        "| Model | Version | NDCG@5 | Precision@5 | Prerequisite violations | Profiles <5 | P50 ms | P95 ms |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["metrics"]:
        lines.append(
            f"| {row['model_name']} | `{row['model_version']}` | "
            f"{row['ndcg_at_5']:.4f} | {row['precision_at_5']:.4f} | "
            f"{row['prerequisite_violations']} | "
            f"{row['profiles_under_5_results']} | "
            f"{row['p50_latency_ms']:.2f} | {row['p95_latency_ms']:.2f} |"
        )
    tuning = report["m2_weight_tuning"]
    lines.extend(
        [
            "",
            "## M2 configuration",
            "",
            f"- Split used for tuning: `{tuning.get('split') or 'none'}`",
            f"- Selected weights (S/G/L): `{tuning['selected_weights']}`",
            f"- Latency benchmark: {report['latency_benchmark']['warmup_runs_per_model']} "
            f"warmups + {report['latency_benchmark']['measured_runs_per_model']} "
            f"measurements per model on "
            f"{report['latency_benchmark']['benchmark_course_catalog_count']} "
            "catalog courses.",
            f"- Latency scope: {report['latency_scope']}.",
            "",
            "## Acceptance targets",
            "",
            "```json",
            json.dumps(report["goal_assessment"], ensure_ascii=False, indent=2),
            "```",
            "",
            "Metrics are calculated on the held-out test learners only. Tuning, "
            "when enabled, uses dev learners only; test labels are never used "
            "for weight selection.",
            "",
        ]
    )
    return "\n".join(lines)


def build_persistence_payload(report: Mapping[str, Any]) -> dict[str, Any]:
    shared_metadata = {
        key: value
        for key, value in report.items()
        if key
        not in {
            "schema_version",
            "evaluation_batch_id",
            "created_at",
            "dataset_version_id",
            "evaluation_split",
            "top_k",
            "catalog_course_count",
            "test_profile_count",
            "labeled_pair_count_test",
            "metrics",
            "per_model_latency_samples_ms",
        }
    }
    payload = {
        "schema_version": report["schema_version"],
        "evaluation_batch_id": report["evaluation_batch_id"],
        "created_at": report["created_at"],
        "dataset_version_id": report["dataset_version_id"],
        "evaluation_split": report["evaluation_split"],
        "top_k": report["top_k"],
        "course_count": report["catalog_course_count"],
        "profile_count": report["test_profile_count"],
        "labeled_pair_count": report["labeled_pair_count_test"],
        "evaluation_metadata": shared_metadata,
        "metrics": [
            {
                **metric,
                "evaluation_metadata": {
                    "latency_samples_ms": report["per_model_latency_samples_ms"][
                        metric["model_name"]
                    ]
                },
            }
            for metric in report["metrics"]
        ],
    }
    return payload


def persist_report(report: Mapping[str, Any], endpoint: str, api_key: str) -> None:
    if not endpoint.strip() or not api_key.strip():
        raise ValueError("evaluation API URL and internal API key are required")
    request = Request(
        endpoint,
        data=json.dumps(
            build_persistence_payload(report),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Internal-API-Key": api_key,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            if response.status not in (200, 201):
                raise RuntimeError(
                    f"evaluation persistence returned unexpected HTTP {response.status}"
                )
    except HTTPError as error:
        detail = error.read(2048).decode("utf-8", errors="replace")
        raise RuntimeError(
            f"evaluation persistence failed with HTTP {error.code}: {detail}"
        ) from error
    except URLError as error:
        raise RuntimeError(f"evaluation persistence request failed: {error.reason}") from error


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--courses", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--min-courses", type=int, default=250)
    parser.add_argument("--min-labeled-pairs", type=int, default=300)
    parser.add_argument("--warmup-runs", type=int, default=10)
    parser.add_argument("--measured-runs", type=int, default=100)
    parser.add_argument("--tune-m2-on-dev", action="store_true")
    parser.add_argument(
        "--persist-url",
        default=os.environ.get("AI_EVALUATION_API_URL"),
        help="Evaluation batch endpoint; defaults to AI_EVALUATION_API_URL",
    )
    args = parser.parse_args()
    report = run_evaluation(
        courses_path=args.courses,
        ground_truth_path=args.ground_truth,
        output_dir=args.output_dir,
        dataset_version_id=args.dataset_version,
        min_course_count=args.min_courses,
        min_labeled_pairs=args.min_labeled_pairs,
        warmup_runs=args.warmup_runs,
        measured_runs=args.measured_runs,
        tune_m2_on_dev=args.tune_m2_on_dev,
    )
    print(f"JSON report: {args.output_dir / 'model-evaluation-report.json'}")
    print(f"Markdown report: {args.output_dir / 'model-evaluation-report.md'}")
    if args.persist_url:
        api_key = os.environ.get("AI_INTERNAL_API_KEY", "")
        persist_report(report, args.persist_url, api_key)
        print("Evaluation metrics persisted to ModelEvaluations.")


if __name__ == "__main__":
    main()
