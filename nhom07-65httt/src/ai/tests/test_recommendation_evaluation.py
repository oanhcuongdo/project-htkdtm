import pytest

from src.recommendations.evaluation import (
    ModelEvaluationRun,
    benchmark_latency,
    compare_model_runs,
)


VERSION_ID = "00000000-0000-4000-8000-000000000003"


def model_run(
    model_name: str,
    ranking: tuple[str, ...],
    *,
    candidates: tuple[str, ...] = ("course-a", "course-b", "course-c"),
    latency_ms: float = 10.0,
) -> ModelEvaluationRun:
    return ModelEvaluationRun(
        model_name=model_name,
        model_version=f"{model_name}-v1",
        dataset_version_id=VERSION_ID,
        filtered_candidate_ids={"learner-1": candidates},
        ranked_course_ids={"learner-1": ranking},
        latency_ms_by_profile={"learner-1": latency_ms},
    )


def test_comparison_uses_same_filtered_candidates_and_reports_metrics():
    metrics = compare_model_runs(
        relevance_by_profile={
            "learner-1": {"course-a": 2, "course-b": 1, "course-filtered-out": 2}
        },
        runs=[
            model_run("M0", ("course-b", "course-a"), latency_ms=20),
            model_run("M1", ("course-a", "course-b"), latency_ms=12),
        ],
        top_k=2,
    )

    assert metrics["M1"].ndcg_at_k > metrics["M0"].ndcg_at_k
    assert metrics["M0"].precision_at_k == metrics["M1"].precision_at_k == 1.0
    assert metrics["M1"].p95_latency_ms == 12
    assert metrics["M0"].profiles_under_top_k == 0


def test_comparison_rejects_different_filter_results():
    with pytest.raises(ValueError, match="same filtered candidate IDs"):
        compare_model_runs(
            relevance_by_profile={"learner-1": {"course-a": 1}},
            runs=[
                model_run("M0", ("course-a",)),
                model_run("M1", ("course-b",), candidates=("course-b",)),
            ],
        )


def test_comparison_rejects_unfiltered_model_output():
    with pytest.raises(ValueError, match="outside the shared filter"):
        compare_model_runs(
            relevance_by_profile={"learner-1": {"course-a": 1}},
            runs=[
                model_run("M1", ("not-filtered",)),
            ],
        )


def test_comparison_rejects_different_dataset_versions():
    other_version_run = ModelEvaluationRun(
        model_name="M1",
        model_version="M1-v1",
        dataset_version_id="00000000-0000-4000-8000-000000000004",
        filtered_candidate_ids={"learner-1": ("course-a", "course-b", "course-c")},
        ranked_course_ids={"learner-1": ("course-a",)},
        latency_ms_by_profile={"learner-1": 10.0},
    )
    with pytest.raises(ValueError, match="same dataset_version_id"):
        compare_model_runs(
            relevance_by_profile={"learner-1": {"course-a": 1}},
            runs=[model_run("M0", ("course-a",)), other_version_run],
        )


def test_latency_benchmark_runs_warmup_and_returns_measured_samples():
    calls = 0

    def run_once() -> None:
        nonlocal calls
        calls += 1

    samples = benchmark_latency(run_once, warmup_runs=2, measured_runs=3)

    assert calls == 5
    assert len(samples) == 3
    assert all(sample >= 0 for sample in samples)


def test_latency_benchmark_requires_measured_runs():
    with pytest.raises(ValueError, match="at least 1"):
        benchmark_latency(lambda: None, measured_runs=0)


def test_comparison_uses_repeated_latency_samples_and_counts_violations():
    run = ModelEvaluationRun(
        model_name="M0",
        model_version="M0-v1",
        dataset_version_id=VERSION_ID,
        filtered_candidate_ids={"learner-1": ("course-a", "course-b")},
        ranked_course_ids={"learner-1": ("course-a",)},
        latency_ms_by_profile={"learner-1": 999.0},
        latency_samples_ms=(10.0, 20.0, 30.0, 40.0, 50.0),
        prerequisite_violations_by_profile={"learner-1": 2},
    )

    metrics = compare_model_runs(
        relevance_by_profile={"learner-1": {"course-a": 1}},
        runs=(run,),
    )["M0"]

    assert metrics.p50_latency_ms == 30.0
    assert metrics.p95_latency_ms == 50.0
    assert metrics.prerequisite_violations == 2
