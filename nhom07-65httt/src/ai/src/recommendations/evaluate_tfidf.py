"""Run M0 over every profile in a JSON evaluation set and export ranked results."""

import argparse
import csv
import hashlib
import json
import math
from dataclasses import replace
from pathlib import Path
import platform
from typing import Mapping, Sequence

import sklearn

from src.recommendations.candidate_filter import (
    CourseCandidate,
    StudentProfile as FilterStudentProfile,
    filter_candidates,
    resolve_candidate_course_ids,
)
from src.recommendations.tfidf_baseline import (
    MODEL_VERSION,
    VECTORIZER_CONFIG,
    CourseDocument,
    LearnerProfile,
    TfidfBaseline,
    terms_from_value,
)


def _read_json_records(path: Path, collection_name: str) -> list[Mapping[str, object]]:
    with path.open(encoding="utf-8-sig") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array of {collection_name}")
    if any(not isinstance(item, dict) for item in data):
        raise ValueError(f"every {collection_name} record in {path} must be an object")
    return data


def _required_string(record: Mapping[str, object], field: str, source: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{source}.{field} must be a non-empty string")
    return value.strip()


def _optional_string(
    record: Mapping[str, object], field: str, source: str
) -> str | None:
    value = record.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{source}.{field} must be a string or null")
    return value


def _popularity_score(record: Mapping[str, object], source: str) -> float | None:
    value = record.get("popularity_score")
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{source}.popularity_score must be a number or null")
    score = float(value)
    if not math.isfinite(score) or score < 0:
        raise ValueError(f"{source}.popularity_score must be finite and non-negative")
    return score


def _parse_courses(records: Sequence[Mapping[str, object]]) -> tuple[CourseDocument, ...]:
    courses = []
    for index, record in enumerate(records):
        source = f"courses[{index}]"
        courses.append(
            CourseDocument(
                course_id=_required_string(record, "course_id", source),
                title=_required_string(record, "title", source),
                description=_optional_string(record, "description", source),
                skills=terms_from_value(record.get("skills"), field_name=f"{source}.skills"),
                direct_skills=terms_from_value(
                    record.get("direct_skills"), field_name=f"{source}.direct_skills"
                ),
                inferred_skills=terms_from_value(
                    record.get("inferred_skills"),
                    field_name=f"{source}.inferred_skills",
                ),
                popularity_score=_popularity_score(record, source),
                skill_ids=_optional_string_tuple(record, "skill_ids", source),
                level=_optional_string(record, "level", source),
            )
        )
    return tuple(courses)


def _optional_number(
    record: Mapping[str, object],
    field: str,
    source: str,
) -> float | None:
    value = record.get(field)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{source}.{field} must be a number or null")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{source}.{field} must be finite and non-negative")
    return number


def _optional_integer(
    record: Mapping[str, object],
    field: str,
    source: str,
) -> int | None:
    value = record.get(field)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{source}.{field} must be a non-negative integer or null")
    return value


def _optional_string_tuple(
    record: Mapping[str, object],
    field: str,
    source: str,
) -> tuple[str, ...] | None:
    value = record.get(field)
    if value is None:
        return None
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ValueError(f"{source}.{field} must be a list of non-empty strings or null")
    return tuple(item.strip() for item in value)


def _parse_candidates(
    records: Sequence[Mapping[str, object]],
) -> tuple[CourseCandidate, ...]:
    candidates = []
    for index, record in enumerate(records):
        source = f"courses[{index}]"
        candidates.append(
            CourseCandidate(
                course_id=_required_string(record, "course_id", source),
                approval_status=_optional_string(record, "approval_status", source),
                offer_type=_optional_string(record, "offer_type", source),
                price_amount=_optional_number(record, "price_amount", source),
                price_currency=_optional_string(record, "price_currency", source),
                required_hours_per_week=_optional_number(
                    record, "required_hours_per_week", source
                ),
                duration_minutes=_optional_integer(
                    record, "duration_minutes", source
                ),
                popularity_score=_popularity_score(record, source),
            )
        )
    return tuple(candidates)


def _parse_course_prerequisites(
    records: Sequence[Mapping[str, object]],
) -> dict[str, tuple[str, ...] | None]:
    prerequisites: dict[str, tuple[str, ...] | None] = {}
    for index, record in enumerate(records):
        source = f"courses[{index}]"
        course_id = _required_string(record, "course_id", source)
        raw_ids = record.get("prerequisite_course_ids")
        if raw_ids is None:
            prerequisites[course_id] = None
        elif not isinstance(raw_ids, list) or any(
            not isinstance(prerequisite_id, str) for prerequisite_id in raw_ids
        ):
            raise ValueError(
                f"{source}.prerequisite_course_ids must be a list of strings or null"
            )
        else:
            prerequisites[course_id] = tuple(raw_ids)
    return prerequisites


def _string_ids(
    record: Mapping[str, object],
    field: str,
    source: str,
) -> tuple[str, ...] | None:
    value = record.get(field)
    if value is None:
        return None
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{source}.{field} must be a list of strings or null")
    return tuple(value)


def _filter_profile(record: Mapping[str, object], source: str) -> FilterStudentProfile:
    raw_constraints = record.get("constraints")
    if raw_constraints is None:
        constraints: Mapping[str, object] = {}
    elif isinstance(raw_constraints, dict):
        constraints = raw_constraints
    else:
        raise ValueError(f"{source}.constraints must be an object or null")
    profile_record_value = record.get("profile")
    if profile_record_value is None:
        profile_record = record
    elif isinstance(profile_record_value, dict):
        profile_record = profile_record_value
    else:
        raise ValueError(f"{source}.profile must be an object or null")

    raw_allowed_types = constraints.get("allowed_offer_types")
    if raw_allowed_types is None:
        allowed_types = None
    elif not isinstance(raw_allowed_types, list) or any(
        not isinstance(value, str) for value in raw_allowed_types
    ):
        raise ValueError(
            f"{source}.constraints.allowed_offer_types must be a list of strings or null"
        )
    else:
        allowed_types = tuple(raw_allowed_types)

    raw_exclude_history = constraints.get("exclude_enrolled_or_completed")
    if raw_exclude_history is not None and not isinstance(raw_exclude_history, bool):
        raise ValueError(
            f"{source}.constraints.exclude_enrolled_or_completed must be a boolean or null"
        )
    goals_value = profile_record.get("goals")
    skills_value = profile_record.get("current_skills")
    goals = (
        None
        if goals_value is None
        else terms_from_value(goals_value, field_name=f"{source}.profile.goals")
    )
    current_skills = (
        None
        if skills_value is None
        else terms_from_value(
            skills_value, field_name=f"{source}.profile.current_skills"
        )
    )
    return FilterStudentProfile(
        goals=goals,
        current_skills=current_skills,
        target_level=_optional_string(
            profile_record, "target_level", f"{source}.profile"
        ),
        allowed_offer_types=allowed_types,
        purchased_course_ids=_string_ids(
            constraints, "purchased_course_ids", f"{source}.constraints"
        ),
        enrolled_course_ids=_string_ids(
            constraints, "enrolled_course_ids", f"{source}.constraints"
        ),
        completed_course_ids=_string_ids(
            constraints, "completed_course_ids", f"{source}.constraints"
        ),
        exclude_course_ids=_string_ids(
            constraints, "exclude_course_ids", f"{source}.constraints"
        ),
        exclude_enrolled_or_completed=raw_exclude_history,
        max_budget_amount=_optional_number(
            constraints, "max_budget_amount", f"{source}.constraints"
        ),
        budget_currency=_optional_string(
            constraints, "currency", f"{source}.constraints"
        ),
        available_hours_per_week=_optional_number(
            constraints, "available_hours_per_week", f"{source}.constraints"
        ),
    )


def _parse_profiles(
    records: Sequence[Mapping[str, object]],
) -> tuple[LearnerProfile, ...]:
    profiles = []
    for index, record in enumerate(records):
        source = f"profiles[{index}]"
        raw_profile = record.get("profile")
        if raw_profile is None:
            profile_record = record
        elif isinstance(raw_profile, dict):
            profile_record = raw_profile
        else:
            raise ValueError(f"{source}.profile must be an object or null")
        candidate_ids = record.get(
            "candidate_course_ids",
            profile_record.get("candidate_course_ids"),
        )
        if candidate_ids is not None and (
            not isinstance(candidate_ids, list)
            or any(not isinstance(course_id, str) for course_id in candidate_ids)
        ):
            raise ValueError(
                f"{source}.candidate_course_ids must be a list of strings or null"
            )
        profiles.append(
            LearnerProfile(
                learner_key=_required_string(record, "learner_key", source),
                goals=terms_from_value(
                    profile_record.get("goals"),
                    field_name=f"{source}.profile.goals",
                ),
                current_skills=terms_from_value(
                    profile_record.get("current_skills"),
                    field_name=f"{source}.profile.current_skills",
                ),
                target_text=_optional_string(
                    profile_record, "target_text", f"{source}.profile"
                ),
                candidate_course_ids=(
                    tuple(candidate_ids) if candidate_ids is not None else None
                ),
            )
        )
    keys = [profile.learner_key for profile in profiles]
    if len(keys) != len(set(keys)):
        raise ValueError("learner_key values must be unique")
    return tuple(profiles)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _candidate_set_hash(course_ids: Sequence[str]) -> str:
    payload = "\n".join(sorted(course_ids)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def evaluate(
    *,
    courses_path: Path,
    profiles_path: Path,
    output_path: Path,
    dataset_version_id: str,
    top_k: int = 5,
) -> Path:
    """Evaluate every profile and write CSV recommendations plus a reproducibility manifest."""
    if not dataset_version_id.strip():
        raise ValueError("dataset_version_id must not be empty")
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    course_records = _read_json_records(courses_path, "courses")
    courses = _parse_courses(course_records)
    profile_records = _read_json_records(profiles_path, "profiles")
    profiles = _parse_profiles(profile_records)
    filter_profiles = tuple(
        _filter_profile(record, f"profiles[{index}]")
        for index, record in enumerate(profile_records)
    )
    filter_candidates_data = _parse_candidates(course_records)
    course_prerequisites = _parse_course_prerequisites(course_records)
    ranker = TfidfBaseline(courses, dataset_version_id=dataset_version_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path = output_path.with_suffix(".metadata.json")
    protected_paths = {
        courses_path.resolve(),
        profiles_path.resolve(),
    }
    if output_path.resolve() in protected_paths or metadata_path.resolve() in protected_paths:
        raise ValueError("output paths must not overwrite the course or profile inputs")

    profile_results = []
    fallback_profile_count = 0
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=(
                "learner_key",
                "model",
                "model_version",
                "dataset_version_id",
                "candidate_set_hash",
                "rank",
                "course_id",
                "score",
                "score_scale",
                "ranking_method",
                "fallback_reason",
                "popularity_score",
            ),
        )
        writer.writeheader()
        for profile, filter_profile in zip(profiles, filter_profiles):
            candidate_filter_result = filter_candidates(
                filter_candidates_data,
                filter_profile,
                course_prerequisites,
                fallback_limit=top_k,
                dataset_version_id=dataset_version_id,
            )
            effective_candidate_ids = resolve_candidate_course_ids(
                profile.candidate_course_ids,
                candidate_filter_result,
            )
            effective_profile = replace(
                profile,
                candidate_course_ids=effective_candidate_ids,
            )
            candidate_hash = _candidate_set_hash(effective_candidate_ids or ())
            ranked = ranker.rank(
                effective_profile,
                top_k=top_k,
                candidate_filter_result=candidate_filter_result,
            )
            fallback_reason = (
                ranked[0].fallback_reason
                if ranked
                else "no_eligible_candidates"
            )
            if not ranked and candidate_filter_result.fallback_reason is not None:
                fallback_reason = candidate_filter_result.fallback_reason
            if fallback_reason is not None and ranked:
                fallback_profile_count += 1
            profile_results.append(
                {
                    "learner_key": profile.learner_key,
                    "candidate_set_hash": candidate_hash,
                    "candidate_count": len(effective_candidate_ids or ()),
                    "eligible_candidate_ids": list(effective_candidate_ids or ()),
                    "result_count": len(ranked),
                    "fallback_reason": fallback_reason,
                    "prerequisite_violations": (
                        candidate_filter_result.prerequisite_violations
                    ),
                    "missing_fields_warning": list(
                        candidate_filter_result.missing_fields_warning
                    ),
                    "rejected_candidates": [
                        {
                            "course_id": rejected.course_id,
                            "reasons": list(rejected.reasons),
                        }
                        for rejected in candidate_filter_result.rejected_candidates
                    ],
                }
            )
            if not ranked:
                writer.writerow(
                    {
                        "learner_key": profile.learner_key,
                        "model": "M0",
                        "model_version": MODEL_VERSION,
                        "dataset_version_id": dataset_version_id,
                        "candidate_set_hash": candidate_hash,
                        "score_scale": "cosine_0_to_1",
                        "ranking_method": "no_eligible_candidates",
                        "fallback_reason": "no_eligible_candidates",
                    }
                )
                continue
            for result in ranked:
                writer.writerow(
                    {
                        "learner_key": profile.learner_key,
                        "model": "M0",
                        "model_version": MODEL_VERSION,
                        "dataset_version_id": dataset_version_id,
                        "candidate_set_hash": candidate_hash,
                        "rank": result.rank,
                        "course_id": result.course.course_id,
                        "score": f"{result.score:.12f}",
                        "score_scale": "cosine_0_to_1",
                        "ranking_method": result.ranking_method,
                        "fallback_reason": result.fallback_reason or "",
                        "popularity_score": (
                            result.course.popularity_score
                            if result.course.popularity_score is not None
                            else ""
                        ),
                    }
                )

    metadata_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "model": "M0",
                "model_version": MODEL_VERSION,
                "dataset_version_id": dataset_version_id,
                "score_scale": "cosine_0_to_1; popularity fallback rows retain score 0",
                "top_k": top_k,
                "deterministic": True,
                "python_version": platform.python_version(),
                "scikit_learn_version": sklearn.__version__,
                "vectorizer_config": VECTORIZER_CONFIG,
                "courses": {
                    "path": str(courses_path),
                    "sha256": _sha256_file(courses_path),
                    "count": len(courses),
                },
                "profiles": {
                    "path": str(profiles_path),
                    "sha256": _sha256_file(profiles_path),
                    "count": len(profiles),
                },
                "output": {
                    "path": str(output_path),
                    "sha256": _sha256_file(output_path),
                    "recommendation_rows": sum(
                        result["result_count"] for result in profile_results
                    ),
                    "profiles_with_fallback": fallback_profile_count,
                    "profiles": profile_results,
                },
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return metadata_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--courses", type=Path, required=True, help="Approved course JSON array")
    parser.add_argument("--profiles", type=Path, required=True, help="Offline test profile JSON array")
    parser.add_argument("--output", type=Path, required=True, help="Top-K CSV output path")
    parser.add_argument("--dataset-version", required=True, help="Immutable course dataset version")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    metadata_path = evaluate(
        courses_path=args.courses,
        profiles_path=args.profiles,
        output_path=args.output,
        dataset_version_id=args.dataset_version,
        top_k=args.top_k,
    )
    print(f"M0 recommendations: {args.output}")
    print(f"Reproducibility manifest: {metadata_path}")


if __name__ == "__main__":
    main()
