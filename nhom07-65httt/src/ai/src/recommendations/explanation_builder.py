"""Build deterministic, source-linked explanations and recommendation traces."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Collection, Mapping, Sequence
from uuid import UUID

from src.recommendations.candidate_filter import (
    CandidateFilterResult,
    CourseCandidate,
    StudentProfile,
    validate_filter_dataset_version,
)
from src.recommendations.m1_semantic import (
    M1RecommendationResult,
)
from src.recommendations.m2_hybrid import (
    M2RecommendationResult,
    WeightedTargetSkill,
)
from src.recommendations.tfidf_baseline import (
    MODEL_VERSION,
    CourseDocument,
    LearnerProfile,
    RankedCourse,
)


@dataclass(frozen=True)
class RankedItemEvidence:
    course: CourseDocument
    rank: int
    score: float | None
    score_scale: str
    ranking_method: str
    dataset_version_id: str
    model_version: str
    score_components: Mapping[str, float | None] | None = None
    score_metadata: Mapping[str, object] | None = None
    fallback_reason: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.rank, bool) or not isinstance(self.rank, int) or self.rank < 1:
            raise ValueError("rank must be a positive integer")
        if self.score is not None and (
            isinstance(self.score, bool)
            or not isinstance(self.score, (int, float))
            or not math.isfinite(self.score)
        ):
            raise ValueError("score must be a finite number or null")
        if (
            not isinstance(self.score_scale, str)
            or not self.score_scale.strip()
            or not isinstance(self.ranking_method, str)
            or not self.ranking_method.strip()
        ):
            raise ValueError("score_scale and ranking_method must not be empty")
        if self.score_components is not None:
            for name, value in self.score_components.items():
                if not isinstance(name, str) or not name.strip():
                    raise ValueError("score component names must not be empty")
                if value is not None and (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                ):
                    raise ValueError(
                        f"score component {name} must be finite or null"
                    )


def ranked_items_from_m0(
    ranked_courses: Sequence[RankedCourse],
    *,
    dataset_version_id: str,
) -> tuple[RankedItemEvidence, ...]:
    return tuple(
        RankedItemEvidence(
            course=item.course,
            rank=item.rank,
            score=item.score,
            score_scale="cosine_similarity",
            ranking_method=item.ranking_method,
            dataset_version_id=dataset_version_id,
            model_version=MODEL_VERSION,
            fallback_reason=item.fallback_reason,
        )
        for item in ranked_courses
    )


def ranked_items_from_m1(
    result: M1RecommendationResult,
    courses: Sequence[CourseDocument],
) -> tuple[RankedItemEvidence, ...]:
    courses_by_id = {course.course_id: course for course in courses}
    if len(courses_by_id) != len(courses):
        raise ValueError("course catalog IDs must be unique")
    return tuple(
        RankedItemEvidence(
            course=_course_for_ranked_id(item.course_id, courses_by_id),
            rank=item.rank,
            score=item.score,
            score_scale=result.score_scale,
            ranking_method=(
                "semantic_cosine" if item.score is not None else "popularity_fallback"
            ),
            dataset_version_id=result.dataset_version_id,
            model_version=result.model_version,
            fallback_reason=result.fallback_reason,
        )
        for item in result.ranked_courses
    )


def ranked_items_from_m2(
    result: M2RecommendationResult,
) -> tuple[RankedItemEvidence, ...]:
    return tuple(
        RankedItemEvidence(
            course=item.course,
            rank=item.rank,
            score=item.components.score,
            score_scale=result.score_scale,
            ranking_method=(
                "m2_hybrid"
                if item.components.score is not None
                else "popularity_fallback"
            ),
            dataset_version_id=result.dataset_version_id,
            model_version=result.model_version,
            score_components=item.components.as_dict(),
            score_metadata={
                "effective_weights": item.components.effective_weights_as_dict(),
                "completeness": item.components.completeness,
            },
            fallback_reason=result.semantic_fallback_reason,
        )
        for item in result.ranked_courses
    )


def build_recommendation_trace(
    *,
    request_id: str | UUID,
    model_name: str,
    model_version: str,
    dataset_version_id: str,
    top_k: int,
    learner_profile: LearnerProfile,
    ranked_items: Sequence[RankedItemEvidence],
    candidate_filter_result: CandidateFilterResult,
    target_skills: Sequence[WeightedTargetSkill] | None = None,
    current_skill_ids: Collection[str] | None = None,
    target_level: str | None = None,
    model_config: Mapping[str, object] | None = None,
    student_id: str | UUID | None = None,
    learner_key: str | None = None,
    created_at: datetime | None = None,
) -> dict[str, object]:
    """Create the immutable JSON trace consumed by the backend persistence layer."""
    request_uuid = _parse_uuid(request_id, "request_id")
    student_uuid = (
        _parse_uuid(student_id, "student_id") if student_id is not None else None
    )
    if student_uuid is not None and learner_key is not None:
        raise ValueError("provide student_id or learner_key, not both")
    supplied_learner_key = (
        learner_profile.learner_key if learner_key is None else learner_key
    )
    trace_learner_key = (
        None
        if student_uuid is not None
        else _required_text(supplied_learner_key, "learner_key")
    )
    model_name = _required_text(model_name, "model_name").upper()
    if model_name not in {"M0", "M1", "M2"}:
        raise ValueError("model_name must be M0, M1, or M2")
    model_version = _required_text(model_version, "model_version")
    dataset_version_id = _required_text(dataset_version_id, "dataset_version_id")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
        raise ValueError("top_k must be a positive integer")
    validate_filter_dataset_version(candidate_filter_result, dataset_version_id)
    if any(
        item.dataset_version_id != dataset_version_id
        or item.model_version != model_version
        for item in ranked_items
    ):
        raise ValueError("ranked item model/data versions do not match trace versions")

    item_ranks = [item.rank for item in ranked_items]
    item_course_ids = [item.course.course_id for item in ranked_items]
    eligible_ids = set(candidate_filter_result.eligible_candidate_ids)
    if len(item_ranks) != len(set(item_ranks)):
        raise ValueError("ranked items must have unique ranks")
    if len(item_course_ids) != len(set(item_course_ids)):
        raise ValueError("ranked items must have unique course IDs")
    if len(ranked_items) > top_k or any(rank > top_k for rank in item_ranks):
        raise ValueError("ranked items must not exceed top_k")
    if any(course_id not in eligible_ids for course_id in item_course_ids):
        raise ValueError("ranked items must belong to the shared eligible candidate set")

    filter_profile = candidate_filter_result.profile_snapshot
    target_level = target_level if target_level is not None else filter_profile.target_level
    course_prerequisites = (
        dict(candidate_filter_result.course_prerequisites_snapshot)
        if candidate_filter_result.course_prerequisites_snapshot is not None
        else None
    )
    candidate_by_id = {
        candidate.course_id: candidate for candidate in candidate_filter_result.candidates
    }
    normalized_targets = _normalized_target_skills(target_skills)
    prerequisite_snapshot = (
        {
            course_id: list(prerequisites)
            if prerequisites is not None
            else None
            for course_id, prerequisites in candidate_filter_result.course_prerequisites_snapshot
        }
        if candidate_filter_result.course_prerequisites_snapshot is not None
        else None
    )
    item_traces = [
        _build_item_trace(
            item=item,
            candidate=candidate_by_id[item.course.course_id],
            filter_profile=filter_profile,
            target_skills=normalized_targets,
            current_skill_ids=current_skill_ids,
            target_level=target_level,
            course_prerequisites=course_prerequisites,
            shared_warnings=candidate_filter_result.missing_fields_warning,
        )
        for item in sorted(ranked_items, key=lambda value: value.rank)
    ]
    timestamp = created_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("created_at must be timezone-aware")
    model_config_snapshot = dict(model_config or {})
    trace: dict[str, object] = {
        "request_id": str(request_uuid),
        "student_id": str(student_uuid) if student_uuid is not None else None,
        "learner_key": trace_learner_key,
        "model_name": model_name,
        "model_version": model_version,
        "dataset_version_id": dataset_version_id,
        "created_at": timestamp.astimezone(timezone.utc).isoformat(),
        "candidate_set_hash": candidate_filter_result.candidate_set_hash,
        "top_k": top_k,
        "model_config": model_config_snapshot,
        "input_snapshot": {
            "learner_profile": _learner_profile_snapshot(learner_profile),
            "filter_profile": _filter_profile_snapshot(filter_profile),
            "target_skills": [
                {
                    "skill_id": skill.skill_id,
                    "label": skill.label,
                    "weight": skill.weight,
                }
                for skill in normalized_targets
            ]
            if normalized_targets is not None
            else None,
            "current_skill_ids": _sorted_or_none(current_skill_ids),
            "target_level": target_level,
            "course_prerequisites": prerequisite_snapshot,
        },
        "filter_snapshot": {
            "input_candidate_ids": list(candidate_filter_result.input_candidate_ids),
            "eligible_candidate_ids": list(
                candidate_filter_result.eligible_candidate_ids
            ),
            "course_prerequisites": prerequisite_snapshot,
            "rejected_candidates": [
                {
                    "course_id": rejected.course_id,
                    "reasons": list(rejected.reasons),
                }
                for rejected in candidate_filter_result.rejected_candidates
            ],
            "missing_fields_warning": list(
                candidate_filter_result.missing_fields_warning
            ),
            "fallback_reason": candidate_filter_result.fallback_reason,
            "prerequisite_violations": candidate_filter_result.prerequisite_violations,
            "candidate_set_hash": candidate_filter_result.candidate_set_hash,
        },
        "items": item_traces,
    }
    json.dumps(trace, sort_keys=True, allow_nan=False)
    return trace


def _build_item_trace(
    *,
    item: RankedItemEvidence,
    candidate: CourseCandidate,
    filter_profile: StudentProfile,
    target_skills: tuple[WeightedTargetSkill, ...] | None,
    current_skill_ids: Collection[str] | None,
    target_level: str | None,
    course_prerequisites: Mapping[str, Collection[str] | None] | None,
    shared_warnings: Sequence[str],
) -> dict[str, object]:
    course = item.course
    warnings = set(shared_warnings)
    claims: list[dict[str, object]] = []

    skill_items: list[dict[str, object]] = []
    if target_skills is None:
        skill_status = "unknown"
        warnings.add("profile.target_skills")
    elif not target_skills:
        skill_status = "no_target_skills"
    elif current_skill_ids is None or course.skill_ids is None:
        skill_status = "unknown"
        if current_skill_ids is None:
            warnings.add("profile.current_skill_ids")
        if course.skill_ids is None:
            warnings.add(f"courses.{course.course_id}.skill_ids")
    else:
        skill_status = "known"
        current_ids = set(current_skill_ids)
        course_ids = set(course.skill_ids)
        skill_items = [
            {
                "skill_id": skill.skill_id,
                "label": skill.label,
                "weight": skill.weight,
                "source_fields": [
                    "profile.target_skills",
                    "profile.current_skill_ids",
                    f"courses.{course.course_id}.skill_ids",
                ],
            }
            for skill in target_skills
            if skill.skill_id not in current_ids and skill.skill_id in course_ids
        ]
        if skill_items:
            labels = ", ".join(str(skill["label"]) for skill in skill_items)
            claims.append(
                {
                    "type": "skill_gap",
                    "text": f"Kỹ năng mục tiêu được khóa học bao phủ: {labels}.",
                    "value": skill_items,
                    "source_fields": [
                        "profile.target_skills",
                        "profile.current_skill_ids",
                        f"courses.{course.course_id}.skill_ids",
                    ],
                }
            )

    normalized_target = _normalized_level(target_level)
    normalized_course = _normalized_level(course.level)
    if normalized_target == "ALL_LEVELS":
        raise ValueError("target_level must be a specific proficiency level")
    if normalized_target is None:
        warnings.add("profile.target_level")
    if normalized_course is None:
        warnings.add(f"courses.{course.course_id}.level")
    if normalized_target is None or normalized_course is None:
        level_evidence: dict[str, object] = {
            "target_level": normalized_target,
            "course_level": normalized_course,
            "fit": None,
            "source_fields": ["profile.target_level", f"courses.{course.course_id}.level"],
        }
    else:
        level_fit = _level_fit(normalized_course, normalized_target)
        level_evidence = {
            "target_level": normalized_target,
            "course_level": normalized_course,
            "fit": level_fit,
            "source_fields": ["profile.target_level", f"courses.{course.course_id}.level"],
        }
        claims.append(
            {
                "type": "level_fit",
                "text": (
                    f"Độ phù hợp cấp độ: người học {normalized_target}, khóa học "
                    f"{normalized_course} ({level_fit:.2f}/1.00)."
                ),
                "value": level_evidence,
                "source_fields": level_evidence["source_fields"],
            }
        )

    prerequisite_evidence = _prerequisite_evidence(
        course.course_id,
        filter_profile.completed_course_ids,
        course_prerequisites,
        warnings,
    )
    if prerequisite_evidence["verified"] is True:
        required_ids = prerequisite_evidence["required_course_ids"]
        if required_ids:
            text = "Đã hoàn thành các khóa tiên quyết: " + ", ".join(required_ids) + "."
        else:
            text = "Đã xác nhận khóa học không có tiên quyết."
        claims.append(
            {
                "type": "prerequisite",
                "text": text,
                "value": prerequisite_evidence,
                "source_fields": prerequisite_evidence["source_fields"],
            }
        )

    price_evidence = _price_evidence(candidate, filter_profile, warnings)
    if candidate.price_amount is not None and candidate.price_currency is not None:
        amount = candidate.price_amount
        currency = candidate.price_currency
        budget = filter_profile.max_budget_amount
        suffix = ""
        if price_evidence["within_budget"] is True:
            suffix = f"; trong ngân sách {budget:g} {currency}"
        elif price_evidence["within_budget"] is False:
            suffix = f"; vượt ngân sách {budget:g} {currency}"
        claims.append(
            {
                "type": "price",
                "text": f"Giá khóa học: {amount:g} {currency}{suffix}.",
                "value": price_evidence,
                "source_fields": price_evidence["source_fields"],
            }
        )

    time_evidence = _time_evidence(candidate, filter_profile, warnings)
    time_text = _time_summary(time_evidence)
    if time_text is not None:
        claims.append(
            {
                "type": "time",
                "text": time_text,
                "value": time_evidence,
                "source_fields": time_evidence["source_fields"],
            }
        )

    warnings.update(
        _course_metadata_warnings(candidate, course.course_id)
    )
    explanation = {
        "claims": claims,
        "skill_gaps": {"status": skill_status, "items": skill_items},
        "level_fit": level_evidence,
        "prerequisites": prerequisite_evidence,
        "price": price_evidence,
        "time": time_evidence,
        "missing_fields_to_confirm": sorted(warnings),
    }
    return {
        "course_id": course.course_id,
        "rank": item.rank,
        "score": item.score,
        "score_scale": item.score_scale,
        "ranking_method": item.ranking_method,
        "fallback_reason": item.fallback_reason,
        "score_components": (
            dict(item.score_components) if item.score_components is not None else None
        ),
        "score_metadata": (
            dict(item.score_metadata) if item.score_metadata is not None else None
        ),
        "course_snapshot": {
            "title": course.title,
            "description": course.description,
            "skills": list(course.skills),
            "direct_skills": list(course.direct_skills),
            "inferred_skills": list(course.inferred_skills),
            "skill_ids": list(course.skill_ids) if course.skill_ids is not None else None,
            "level": course.level,
            "approval_status": candidate.approval_status,
            "offer_type": candidate.offer_type,
            "price_amount": candidate.price_amount,
            "price_currency": candidate.price_currency,
            "duration_minutes": candidate.duration_minutes,
            "required_hours_per_week": candidate.required_hours_per_week,
            "popularity_score": candidate.popularity_score,
        },
        "explanation": explanation,
    }


def _prerequisite_evidence(
    course_id: str,
    completed_course_ids: Collection[str] | None,
    course_prerequisites: Mapping[str, Collection[str] | None] | None,
    warnings: set[str],
) -> dict[str, object]:
    source_fields = [
        f"course_prerequisites.{course_id}",
        "profile.completed_course_ids",
    ]
    if (
        course_prerequisites is None
        or course_id not in course_prerequisites
        or course_prerequisites[course_id] is None
    ):
        warnings.add(f"course_prerequisites.{course_id}")
        return {
            "required_course_ids": None,
            "completed_required_course_ids": None,
            "verified": None,
            "source_fields": source_fields,
        }

    required_ids = sorted(set(course_prerequisites[course_id] or ()))
    if not required_ids:
        return {
            "required_course_ids": [],
            "completed_required_course_ids": [],
            "verified": True,
            "source_fields": source_fields,
        }
    if completed_course_ids is None:
        warnings.add("profile.completed_course_ids")
        return {
            "required_course_ids": required_ids,
            "completed_required_course_ids": None,
            "verified": None,
            "source_fields": source_fields,
        }
    completed = set(completed_course_ids)
    completed_required = [course_id for course_id in required_ids if course_id in completed]
    return {
        "required_course_ids": required_ids,
        "completed_required_course_ids": completed_required,
        "verified": len(completed_required) == len(required_ids),
        "source_fields": source_fields,
    }


def _price_evidence(
    candidate: CourseCandidate,
    profile: StudentProfile,
    warnings: set[str],
) -> dict[str, object]:
    if candidate.price_amount is None:
        warnings.add(f"courses.{candidate.course_id}.price_amount")
    if candidate.price_currency is None:
        warnings.add(f"courses.{candidate.course_id}.price_currency")
    within_budget = None
    if profile.max_budget_amount is not None:
        if candidate.price_amount is None or candidate.price_currency is None:
            warnings.add("profile.max_budget_amount")
        elif candidate.price_currency == profile.budget_currency:
            within_budget = candidate.price_amount <= profile.max_budget_amount
        else:
            warnings.add("profile.budget_currency")
    return {
        "amount": candidate.price_amount,
        "currency": candidate.price_currency,
        "budget_amount": profile.max_budget_amount,
        "budget_currency": profile.budget_currency,
        "within_budget": within_budget,
        "source_fields": [
            f"courses.{candidate.course_id}.price_amount",
            f"courses.{candidate.course_id}.price_currency",
            "profile.max_budget_amount",
            "profile.budget_currency",
        ],
    }


def _time_evidence(
    candidate: CourseCandidate,
    profile: StudentProfile,
    warnings: set[str],
) -> dict[str, object]:
    if candidate.duration_minutes is None:
        warnings.add(f"courses.{candidate.course_id}.duration_minutes")
    if candidate.required_hours_per_week is None:
        warnings.add(f"courses.{candidate.course_id}.required_hours_per_week")
    within_available_hours = None
    if profile.available_hours_per_week is not None:
        if candidate.required_hours_per_week is None:
            warnings.add("profile.available_hours_per_week")
        else:
            within_available_hours = (
                candidate.required_hours_per_week <= profile.available_hours_per_week
            )
    return {
        "duration_minutes": candidate.duration_minutes,
        "required_hours_per_week": candidate.required_hours_per_week,
        "available_hours_per_week": profile.available_hours_per_week,
        "within_available_hours": within_available_hours,
        "source_fields": [
            f"courses.{candidate.course_id}.duration_minutes",
            f"courses.{candidate.course_id}.required_hours_per_week",
            "profile.available_hours_per_week",
        ],
    }


def _time_summary(evidence: Mapping[str, object]) -> str | None:
    summaries = []
    duration = evidence["duration_minutes"]
    if isinstance(duration, int) and not isinstance(duration, bool):
        summaries.append(f"thời lượng {duration} phút")
    required_hours = evidence["required_hours_per_week"]
    available_hours = evidence["available_hours_per_week"]
    if isinstance(required_hours, (int, float)) and not isinstance(
        required_hours, bool
    ):
        text = f"tải học {required_hours:g} giờ/tuần"
        if isinstance(available_hours, (int, float)) and not isinstance(
            available_hours, bool
        ):
            status = (
                "phù hợp"
                if evidence["within_available_hours"] is True
                else "vượt khả năng khai báo"
            )
            text += f" so với {available_hours:g} giờ/tuần ({status})"
        summaries.append(text)
    if not summaries:
        return None
    return "Thông tin thời gian: " + "; ".join(summaries) + "."


def _course_metadata_warnings(candidate: CourseCandidate, course_id: str) -> set[str]:
    warnings = set()
    if candidate.approval_status is None:
        warnings.add(f"courses.{course_id}.approval_status")
    return warnings


def _learner_profile_snapshot(profile: LearnerProfile) -> dict[str, object]:
    return {
        "goals": list(profile.goals),
        "current_skills": list(profile.current_skills),
        "target_text": profile.target_text,
        "candidate_course_ids": (
            list(profile.candidate_course_ids)
            if profile.candidate_course_ids is not None
            else None
        ),
    }


def _filter_profile_snapshot(profile: StudentProfile) -> dict[str, object]:
    return {
        "goals": _sorted_or_none(profile.goals),
        "current_skills": _sorted_or_none(profile.current_skills),
        "target_level": profile.target_level,
        "allowed_offer_types": _sorted_or_none(profile.allowed_offer_types),
        "purchased_course_ids": _sorted_or_none(profile.purchased_course_ids),
        "enrolled_course_ids": _sorted_or_none(profile.enrolled_course_ids),
        "completed_course_ids": _sorted_or_none(profile.completed_course_ids),
        "exclude_course_ids": _sorted_or_none(profile.exclude_course_ids),
        "exclude_enrolled_or_completed": profile.exclude_enrolled_or_completed,
        "max_budget_amount": profile.max_budget_amount,
        "budget_currency": profile.budget_currency,
        "available_hours_per_week": profile.available_hours_per_week,
    }


def _normalized_target_skills(
    target_skills: Sequence[WeightedTargetSkill] | None,
) -> tuple[WeightedTargetSkill, ...] | None:
    if target_skills is None:
        return None
    return tuple(sorted(target_skills, key=lambda skill: skill.skill_id))


def _sorted_or_none(values: Collection[str] | None) -> list[str] | None:
    return sorted(values) if values is not None else None


def _normalized_level(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    if normalized == "ALL_LEVELS" or normalized in {"BEGINNER", "INTERMEDIATE", "ADVANCED"}:
        return normalized
    raise ValueError(f"unsupported course level: {value}")


def _level_fit(course_level: str, target_level: str) -> float:
    levels = ("BEGINNER", "INTERMEDIATE", "ADVANCED")
    if course_level == "ALL_LEVELS":
        return 1.0
    distance = abs(levels.index(course_level) - levels.index(target_level))
    return 1.0 - distance / (len(levels) - 1)


def _required_text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must not be empty")
    return value.strip()


def _parse_uuid(value: str | UUID, field: str) -> UUID:
    try:
        return value if isinstance(value, UUID) else UUID(value)
    except (TypeError, ValueError, AttributeError) as error:
        raise ValueError(f"{field} must be a valid UUID") from error


def _course_for_ranked_id(
    course_id: str,
    courses_by_id: Mapping[str, CourseDocument],
) -> CourseDocument:
    try:
        return courses_by_id[course_id]
    except KeyError as error:
        raise ValueError(f"ranked course {course_id} is missing from course catalog") from error

