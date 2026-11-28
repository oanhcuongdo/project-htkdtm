"""Offline ranking metrics and fair comparison checks for recommender models."""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class ModelEvaluationRun:
    model_name: str
    model_version: str
    dataset_version_id: str
    filtered_candidate_ids: Mapping[str, Sequence[str]]
    ranked_course_ids: Mapping[str, Sequence[str]]
    latency_ms_by_profile: Mapping[str, float]
    latency_samples_ms: Sequence[float] = ()
    prerequisite_violations_by_profile: Mapping[str, int] | None = None


@dataclass(frozen=True)
class RankingMetrics:
    ndcg_at_k: float
    precision_at_k: float
    p50_latency_ms: float
    p95_latency_ms: float
    profiles_under_top_k: int
    prerequisite_violations: int = 0


def benchmark_latency(
    rank_once: Callable[[], object],
    *,
    warmup_runs: int = 10,
    measured_runs: int = 100,
) -> tuple[float, ...]:
    """Return end-to-end latency samples in milliseconds after warmup."""
    if warmup_runs < 0:
        raise ValueError("warmup_runs must not be negative")
    if measured_runs < 1:
        raise ValueError("measured_runs must be at least 1")
    for _ in range(warmup_runs):
        rank_once()

    samples: list[float] = []
    for _ in range(measured_runs):
        started = time.perf_counter()
        rank_once()
        samples.append((time.perf_counter() - started) * 1000)
    return tuple(samples)


def compare_model_runs(
    *,
    relevance_by_profile: Mapping[str, Mapping[str, int]],
    runs: Sequence[ModelEvaluationRun],
    top_k: int = 5,
) -> dict[str, RankingMetrics]:
    """Compare model outputs only when dataset, profiles, and filtered sets match.

    Candidate IDs in each run must come directly from the shared hard-filter
    result. A model output outside that set is treated as an evaluation error,
    not silently dropped from its metrics.
    """
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    if not runs:
        raise ValueError("at least one model run is required")
    model_names = [run.model_name for run in runs]
    if len(model_names) != len(set(model_names)):
        raise ValueError("model_name values must be unique")

    reference = runs[0]
    reference_profiles = set(relevance_by_profile)
    if not reference_profiles:
        raise ValueError("relevance_by_profile must contain evaluation profiles")
    reference_candidates = _validate_run_shape(reference, reference_profiles)

    metrics: dict[str, RankingMetrics] = {}
    for run in runs:
        if run.dataset_version_id != reference.dataset_version_id:
            raise ValueError("all models must use the same dataset_version_id")
        candidate_sets = _validate_run_shape(run, reference_profiles)
        if candidate_sets != reference_candidates:
            raise ValueError(
                f"{run.model_name} did not use the same filtered candidate IDs as "
                f"{reference.model_name}"
            )
        latencies: list[float] = []
        for profile_id in sorted(reference_profiles):
            ranking = run.ranked_course_ids[profile_id]
            candidate_ids = set(candidate_sets[profile_id])
            if len(ranking) != len(set(ranking)):
                raise ValueError(
                    f"{run.model_name} returned duplicate course IDs for {profile_id}"
                )
            invalid_ids = set(ranking) - candidate_ids
            if invalid_ids:
                raise ValueError(
                    f"{run.model_name} returned candidates outside the shared filter "
                    f"for {profile_id}: {', '.join(sorted(invalid_ids))}"
                )
            latency = run.latency_ms_by_profile[profile_id]
            if not math.isfinite(latency) or latency < 0:
                raise ValueError("latency measurements must be finite and non-negative")
            latencies.append(latency)

        per_profile = [
            _ranking_metrics(
                run.ranked_course_ids[profile_id],
                relevance_by_profile[profile_id],
                candidate_sets[profile_id],
                top_k,
            )
            for profile_id in sorted(reference_profiles)
        ]
        latency_samples = tuple(run.latency_samples_ms) or tuple(latencies)
        if any(
            not math.isfinite(latency) or latency < 0
            for latency in latency_samples
        ):
            raise ValueError("latency measurements must be finite and non-negative")
        prerequisite_violations = 0
        if run.prerequisite_violations_by_profile is not None:
            if set(run.prerequisite_violations_by_profile) != reference_profiles:
                raise ValueError(
                    f"{run.model_name}.prerequisite_violations_by_profile must "
                    "contain exactly the evaluation profiles"
                )
            violations = tuple(run.prerequisite_violations_by_profile.values())
            if any(
                isinstance(count, bool) or not isinstance(count, int) or count < 0
                for count in violations
            ):
                raise ValueError("prerequisite violations must be non-negative integers")
            prerequisite_violations = sum(violations)

        metrics[run.model_name] = RankingMetrics(
            ndcg_at_k=math.fsum(item[0] for item in per_profile) / len(per_profile),
            precision_at_k=math.fsum(item[1] for item in per_profile) / len(per_profile),
            p50_latency_ms=_percentile(latency_samples, 0.50),
            p95_latency_ms=_percentile(latency_samples, 0.95),
            profiles_under_top_k=sum(item[2] for item in per_profile),
            prerequisite_violations=prerequisite_violations,
        )
    return metrics


def _validate_run_shape(
    run: ModelEvaluationRun,
    profile_ids: set[str],
) -> dict[str, tuple[str, ...]]:
    expected_profiles = set(profile_ids)
    for label, values in (
        ("filtered_candidate_ids", run.filtered_candidate_ids),
        ("ranked_course_ids", run.ranked_course_ids),
        ("latency_ms_by_profile", run.latency_ms_by_profile),
    ):
        if set(values) != expected_profiles:
            raise ValueError(
                f"{run.model_name}.{label} must contain exactly the evaluation profiles"
            )
    if not run.model_version.strip() or not run.dataset_version_id.strip():
        raise ValueError("model_version and dataset_version_id must not be empty")
    candidate_sets: dict[str, tuple[str, ...]] = {}
    for profile_id, candidate_ids in run.filtered_candidate_ids.items():
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError(
                f"filtered candidate IDs contain duplicates for {profile_id}"
            )
        candidate_sets[profile_id] = tuple(candidate_ids)
    return candidate_sets


def _ranking_metrics(
    ranked_course_ids: Sequence[str],
    relevance: Mapping[str, int],
    filtered_candidate_ids: Sequence[str],
    top_k: int,
) -> tuple[float, float, int]:
    for grade in relevance.values():
        if isinstance(grade, bool) or not isinstance(grade, int) or grade < 0:
            raise ValueError("relevance grades must be non-negative integers")

    eligible_relevance = {
        course_id: relevance.get(course_id, 0)
        for course_id in filtered_candidate_ids
    }
    top = ranked_course_ids[:top_k]
    precision = sum(eligible_relevance.get(course_id, 0) > 0 for course_id in top) / top_k
    dcg = math.fsum(
        (2**eligible_relevance.get(course_id, 0) - 1) / math.log2(index + 2)
        for index, course_id in enumerate(top)
    )
    ideal_grades = sorted(eligible_relevance.values(), reverse=True)[:top_k]
    ideal_dcg = math.fsum(
        (2**grade - 1) / math.log2(index + 2)
        for index, grade in enumerate(ideal_grades)
    )
    ndcg = dcg / ideal_dcg if ideal_dcg else 0.0
    return ndcg, precision, int(len(ranked_course_ids) < top_k)


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        raise ValueError("latency measurements must not be empty")
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]
