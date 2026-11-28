import json

import pytest

from src.recommendations.m1_semantic import M1SemanticRanker
from src.recommendations.run_model_evaluation import (
    build_persistence_payload,
    run_evaluation,
)


DATASET_VERSION = "dataset-eval-v1"


class FixedEncoder:
    def encode(
        self,
        sentences,
        *,
        batch_size,
        show_progress_bar,
        convert_to_numpy,
        normalize_embeddings,
    ):
        return [[1.0, 0.0] for _ in sentences]


def _course(course_id, skill_id, level):
    return {
        "course_id": course_id,
        "title": f"Course {course_id}",
        "description": f"Training for {skill_id}",
        "skills": [skill_id],
        "skill_ids": [skill_id],
        "level": level,
        "approval_status": "approved",
        "offer_type": "ONLINE",
        "price_amount": None,
        "price_currency": None,
        "duration_minutes": 60,
        "required_hours_per_week": None,
        "popularity_score": 1,
        "prerequisite_course_ids": [],
    }


def _learner(learner_key, split, preferred_skill):
    return {
        "learner_key": learner_key,
        "split": split,
        "profile": {
            "goals": [preferred_skill],
            "current_skills": [],
            "target_level": "BEGINNER",
        },
        "constraints": {},
        "target_skills": [
            {"skill_id": preferred_skill, "label": preferred_skill, "weight": 1.0}
        ],
        "current_skill_ids": [],
        "skill_prerequisites": {preferred_skill: []},
        "relevance": {
            "course-a": 2 if preferred_skill == "python" else 0,
            "course-b": 2 if preferred_skill == "sql" else 0,
            "course-c": 1,
        },
    }


def test_runner_exports_test_only_metrics_and_dev_tuned_ablation_report(tmp_path):
    courses_path = tmp_path / "courses.json"
    ground_truth_path = tmp_path / "ground-truth.json"
    output_dir = tmp_path / "out"
    courses_path.write_text(
        json.dumps(
            [
                _course("course-a", "python", "BEGINNER"),
                _course("course-b", "sql", "INTERMEDIATE"),
                _course("course-c", "analytics", "ALL_LEVELS"),
            ]
        ),
        encoding="utf-8",
    )
    ground_truth_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "split_strategy": "group_by_learner",
                "dataset_version_id": DATASET_VERSION,
                "profiles": [
                    _learner("dev-learner", "dev", "python"),
                    _learner("test-learner", "test", "sql"),
                ],
            }
        ),
        encoding="utf-8",
    )
    semantic = M1SemanticRanker(
        cache_dir=tmp_path / "cache",
        model_name="test-encoder",
        model_revision="fixed",
        encoder=FixedEncoder(),
    )

    report = run_evaluation(
        courses_path=courses_path,
        ground_truth_path=ground_truth_path,
        output_dir=output_dir,
        dataset_version_id=DATASET_VERSION,
        warmup_runs=1,
        measured_runs=100,
        min_course_count=3,
        min_labeled_pairs=0,
        tune_m2_on_dev=True,
        semantic_ranker=semantic,
    )

    assert report["evaluation_split"] == "test"
    assert report["dev_profile_count"] == 1
    assert report["test_profile_count"] == 1
    assert report["m2_weight_tuning"]["split"] == "dev"
    assert {row["model_name"] for row in report["metrics"]} == {
        "M0",
        "M1",
        "M2",
        "M2-no-G",
        "M2-no-L",
    }
    assert all(
        len(samples) == 100
        for samples in report["per_model_latency_samples_ms"].values()
    )
    persistence_payload = build_persistence_payload(report)
    assert persistence_payload["evaluation_split"] == "test"
    assert len(persistence_payload["metrics"]) == 5
    assert all(
        len(metric["evaluation_metadata"]["latency_samples_ms"]) == 100
        for metric in persistence_payload["metrics"]
    )
    assert (output_dir / "model-evaluation-report.json").exists()
    assert (output_dir / "model-evaluation-report.md").exists()


def test_runner_rejects_learners_shared_across_splits(tmp_path):
    ground_truth_path = tmp_path / "ground-truth.json"
    ground_truth_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "split_strategy": "group_by_learner",
                "profiles": [
                    _learner("same-learner", "dev", "python"),
                    _learner("same-learner", "test", "sql"),
                ],
            }
        ),
        encoding="utf-8",
    )

    from src.recommendations.run_model_evaluation import load_ground_truth

    with pytest.raises(ValueError, match="only one split"):
        load_ground_truth(
            ground_truth_path,
            dataset_version_id=DATASET_VERSION,
            course_ids={"course-a", "course-b", "course-c"},
        )
