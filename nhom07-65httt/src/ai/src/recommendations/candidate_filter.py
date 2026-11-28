"""Shared hard filters for M0, M1, and M2 recommendation candidates."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Collection, Mapping, Sequence


@dataclass(frozen=True)
class CourseCandidate:
    course_id: str
    approval_status: str | None
    offer_type: str | None
    price_amount: float | None = None
    price_currency: str | None = None
    duration_minutes: int | None = None
    required_hours_per_week: float | None = None
    popularity_score: float | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.course_id, str)
            or not self.course_id.strip()
            or self.course_id != self.course_id.strip()
        ):
            raise ValueError("course_id must be a non-empty string")
        for field_name, value in (
            ("price_amount", self.price_amount),
            ("required_hours_per_week", self.required_hours_per_week),
            ("popularity_score", self.popularity_score),
        ):
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError(f"{field_name} must be finite and non-negative")
        if self.duration_minutes is not None and (
            isinstance(self.duration_minutes, bool)
            or not isinstance(self.duration_minutes, int)
            or self.duration_minutes < 0
        ):
            raise ValueError("duration_minutes must be a non-negative integer or null")
        if self.price_currency is not None and not _is_currency(self.price_currency):
            raise ValueError("price_currency must be a three-letter currency code")
        if self.approval_status is not None and not isinstance(self.approval_status, str):
            raise ValueError("approval_status must be a string or null")
        if self.offer_type is not None and not isinstance(self.offer_type, str):
            raise ValueError("offer_type must be a string or null")


@dataclass(frozen=True)
class StudentProfile:
    goals: Collection[str] | None = None
    current_skills: Collection[str] | None = None
    target_level: str | None = None
    allowed_offer_types: Collection[str] | None = None
    purchased_course_ids: Collection[str] | None = None
    enrolled_course_ids: Collection[str] | None = None
    completed_course_ids: Collection[str] | None = None
    exclude_course_ids: Collection[str] | None = None
    exclude_enrolled_or_completed: bool | None = None
    max_budget_amount: float | None = None
    budget_currency: str | None = None
    available_hours_per_week: float | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "goals",
            "current_skills",
            "purchased_course_ids",
            "enrolled_course_ids",
            "completed_course_ids",
            "exclude_course_ids",
        ):
            values = getattr(self, field_name)
            if values is not None:
                _validate_string_collection(values, field_name=field_name)
        if self.allowed_offer_types is not None:
            _validate_string_collection(
                self.allowed_offer_types, field_name="allowed_offer_types"
            )
        for field_name, value in (
            ("max_budget_amount", self.max_budget_amount),
            ("available_hours_per_week", self.available_hours_per_week),
        ):
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError(f"{field_name} must be finite and non-negative")
        if self.available_hours_per_week == 0:
            raise ValueError("available_hours_per_week must be positive")
        if self.max_budget_amount is not None and self.budget_currency is None:
            raise ValueError("budget_currency is required when max_budget_amount is set")
        if self.budget_currency is not None and not _is_currency(self.budget_currency):
            raise ValueError("budget_currency must be a three-letter currency code")
        if self.exclude_enrolled_or_completed is not None and not isinstance(
            self.exclude_enrolled_or_completed, bool
        ):
            raise ValueError("exclude_enrolled_or_completed must be a boolean or null")
        if self.target_level is not None and not isinstance(self.target_level, str):
            raise ValueError("target_level must be a string or null")


@dataclass(frozen=True)
class RejectedCandidate:
    course_id: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class CandidateFilterResult:
    dataset_version_id: str
    profile_snapshot: StudentProfile
    course_prerequisites_snapshot: tuple[
        tuple[str, tuple[str, ...] | None], ...
    ] | None
    input_candidate_ids: tuple[str, ...]
    candidates: tuple[CourseCandidate, ...]
    fallback_candidates: tuple[CourseCandidate, ...]
    rejected_candidates: tuple[RejectedCandidate, ...]
    missing_fields_warning: tuple[str, ...]
    fallback_reason: str | None
    prerequisite_violations: int
    candidate_set_hash: str

    @property
    def eligible_candidate_ids(self) -> tuple[str, ...]:
        return tuple(candidate.course_id for candidate in self.candidates)


def filter_candidates(
    candidates: Sequence[CourseCandidate],
    profile: StudentProfile,
    course_prerequisites: Mapping[str, Collection[str] | None] | None,
    *,
    dataset_version_id: str,
    fallback_limit: int = 5,
) -> CandidateFilterResult:
    """Apply required hard filters and return a deterministic fallback pool.

    Missing optional learner constraints are fail-open with warnings. Approval
    and prerequisite checks are fail-closed because those cannot be relaxed
    without making an ineligible or prerequisite-violating recommendation.
    """
    if fallback_limit < 1:
        raise ValueError("fallback_limit must be at least 1")
    if not isinstance(dataset_version_id, str) or not dataset_version_id.strip():
        raise ValueError("dataset_version_id must be a non-empty string")
    candidate_ids = [candidate.course_id for candidate in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("candidate course IDs must be unique")

    warnings = _profile_warnings(profile)
    eligible: list[CourseCandidate] = []
    rejected: list[RejectedCandidate] = []
    for candidate in sorted(candidates, key=lambda item: item.course_id):
        reasons: list[str] = []
        approval_status = (
            candidate.approval_status.strip().lower()
            if candidate.approval_status is not None
            else None
        )
        if approval_status != "approved":
            reasons.append(
                "unknown_approval_status"
                if approval_status is None
                else "not_approved"
            )
            if approval_status is None:
                warnings.add(f"courses.{candidate.course_id}.approval_status")

        _apply_offer_filter(candidate, profile, reasons, warnings)
        _apply_history_filters(candidate, profile, reasons, warnings)
        _apply_budget_filter(candidate, profile, reasons, warnings)
        _apply_time_filter(candidate, profile, reasons, warnings)
        _apply_prerequisite_filter(
            candidate,
            profile,
            course_prerequisites,
            reasons,
            warnings,
        )

        if reasons:
            rejected.append(
                RejectedCandidate(
                    course_id=candidate.course_id,
                    reasons=tuple(sorted(set(reasons))),
                )
            )
        else:
            eligible.append(candidate)

    fallback_pool = sorted(
        eligible,
        key=lambda candidate: (
            candidate.popularity_score is None,
            -(candidate.popularity_score or 0.0),
            candidate.course_id,
        ),
    )[:fallback_limit]
    cold_start = not (
        _has_values(profile.goals)
        or _has_values(profile.current_skills)
        or bool(profile.target_level and profile.target_level.strip())
    )
    if not eligible:
        fallback_reason = "no_eligible_candidates"
    elif cold_start:
        fallback_reason = "cold_start"
    else:
        fallback_reason = None

    eligible_ids = tuple(candidate.course_id for candidate in eligible)
    prerequisite_violations = count_prerequisite_violations(
        eligible_ids,
        profile.completed_course_ids,
        course_prerequisites,
    )
    candidate_hash = hashlib.sha256(
        "\n".join(eligible_ids).encode("utf-8")
    ).hexdigest()
    return CandidateFilterResult(
        dataset_version_id=dataset_version_id.strip(),
        profile_snapshot=_snapshot_profile(profile),
        course_prerequisites_snapshot=_snapshot_prerequisites(
            candidates,
            course_prerequisites,
        ),
        input_candidate_ids=tuple(sorted(candidate_ids)),
        candidates=tuple(eligible),
        fallback_candidates=tuple(fallback_pool),
        rejected_candidates=tuple(rejected),
        missing_fields_warning=tuple(sorted(warnings)),
        fallback_reason=fallback_reason,
        prerequisite_violations=prerequisite_violations,
        candidate_set_hash=candidate_hash,
    )


def _snapshot_profile(profile: StudentProfile) -> StudentProfile:
    return StudentProfile(
        goals=_sorted_collection(profile.goals),
        current_skills=_sorted_collection(profile.current_skills),
        target_level=profile.target_level,
        allowed_offer_types=_sorted_collection(profile.allowed_offer_types),
        purchased_course_ids=_sorted_collection(profile.purchased_course_ids),
        enrolled_course_ids=_sorted_collection(profile.enrolled_course_ids),
        completed_course_ids=_sorted_collection(profile.completed_course_ids),
        exclude_course_ids=_sorted_collection(profile.exclude_course_ids),
        exclude_enrolled_or_completed=profile.exclude_enrolled_or_completed,
        max_budget_amount=profile.max_budget_amount,
        budget_currency=profile.budget_currency,
        available_hours_per_week=profile.available_hours_per_week,
    )


def _sorted_collection(values: Collection[str] | None) -> tuple[str, ...] | None:
    return tuple(sorted(values)) if values is not None else None


def _snapshot_prerequisites(
    candidates: Sequence[CourseCandidate],
    prerequisites: Mapping[str, Collection[str] | None] | None,
) -> tuple[tuple[str, tuple[str, ...] | None], ...] | None:
    if prerequisites is None:
        return None
    return tuple(
        (
            candidate.course_id,
            tuple(sorted(set(prerequisite_ids)))
            if prerequisite_ids is not None
            else None,
        )
        for candidate in sorted(candidates, key=lambda item: item.course_id)
        for prerequisite_ids in (prerequisites.get(candidate.course_id),)
    )


def resolve_candidate_course_ids(
    candidate_course_ids: Sequence[str] | None,
    filter_result: CandidateFilterResult | None,
) -> tuple[str, ...] | None:
    """Use shared-filter IDs, optionally narrowed by an existing candidate set."""
    if filter_result is None:
        return candidate_course_ids
    eligible_ids = set(filter_result.eligible_candidate_ids)
    if candidate_course_ids is None:
        return filter_result.eligible_candidate_ids
    requested_ids = set(candidate_course_ids)
    unknown_ids = requested_ids - set(filter_result.input_candidate_ids)
    if unknown_ids:
        raise ValueError(
            "candidate_course_ids contain unknown courses: "
            + ", ".join(sorted(unknown_ids))
        )
    return tuple(sorted(requested_ids & eligible_ids))


def fallback_ordered_candidate_ids(
    filter_result: CandidateFilterResult,
    candidate_course_ids: Collection[str] | None = None,
) -> tuple[str, ...]:
    """Order only eligible fallback candidates using shared popularity metadata."""
    candidate_index = {
        candidate.course_id: candidate for candidate in filter_result.candidates
    }
    selected_ids = (
        set(candidate_index)
        if candidate_course_ids is None
        else set(candidate_course_ids)
    )
    unknown_ids = selected_ids - candidate_index.keys()
    if unknown_ids:
        raise ValueError(
            "fallback candidate IDs are outside the shared filter: "
            + ", ".join(sorted(unknown_ids))
        )
    return tuple(
        sorted(
            selected_ids,
            key=lambda course_id: (
                candidate_index[course_id].popularity_score is None,
                -(candidate_index[course_id].popularity_score or 0.0),
                course_id,
            ),
        )
    )


def validate_filter_dataset_version(
    filter_result: CandidateFilterResult | None,
    dataset_version_id: str,
) -> None:
    if filter_result is not None and filter_result.dataset_version_id != dataset_version_id:
        raise ValueError("candidate filter dataset version does not match ranker")


def count_prerequisite_violations(
    candidate_course_ids: Collection[str],
    completed_course_ids: Collection[str] | None,
    course_prerequisites: Mapping[str, Collection[str] | None] | None,
) -> int:
    """Count eligible courses whose known prerequisites are not completed."""
    violations = 0
    for course_id in candidate_course_ids:
        if course_prerequisites is None or course_id not in course_prerequisites:
            raise ValueError(f"prerequisites are unknown for eligible course {course_id}")
        prerequisites = course_prerequisites[course_id]
        if prerequisites is None:
            raise ValueError(f"prerequisites are unknown for eligible course {course_id}")
        prerequisite_ids = _validate_string_collection(
            prerequisites,
            field_name=f"course_prerequisites[{course_id}]",
        )
        if not prerequisite_ids:
            continue
        if completed_course_ids is None:
            raise ValueError(
                f"completion history is unknown for eligible course {course_id}"
            )
        if set(prerequisite_ids) - set(completed_course_ids):
            violations += 1
    return violations


def _profile_warnings(profile: StudentProfile) -> set[str]:
    warnings: set[str] = set()
    optional_fields = (
        ("allowed_offer_types", profile.allowed_offer_types),
        ("purchased_course_ids", profile.purchased_course_ids),
        ("exclude_course_ids", profile.exclude_course_ids),
        ("max_budget_amount", profile.max_budget_amount),
        ("available_hours_per_week", profile.available_hours_per_week),
    )
    warnings.update(
        f"profile.{field_name}"
        for field_name, value in optional_fields
        if value is None
    )
    if profile.exclude_enrolled_or_completed is None:
        warnings.add("profile.exclude_enrolled_or_completed")
    elif profile.exclude_enrolled_or_completed:
        if profile.enrolled_course_ids is None:
            warnings.add("profile.enrolled_course_ids")
        if profile.completed_course_ids is None:
            warnings.add("profile.completed_course_ids")
    return warnings


def _apply_offer_filter(
    candidate: CourseCandidate,
    profile: StudentProfile,
    reasons: list[str],
    warnings: set[str],
) -> None:
    if profile.allowed_offer_types is None:
        return
    if candidate.offer_type is None:
        reasons.append("unknown_offer_type")
        warnings.add(f"courses.{candidate.course_id}.offer_type")
        return
    allowed = {offer_type.strip().upper() for offer_type in profile.allowed_offer_types}
    if candidate.offer_type.strip().upper() not in allowed:
        reasons.append("offer_type_not_allowed")


def _apply_history_filters(
    candidate: CourseCandidate,
    profile: StudentProfile,
    reasons: list[str],
    warnings: set[str],
) -> None:
    if profile.purchased_course_ids is None:
        pass
    elif candidate.course_id in profile.purchased_course_ids:
        reasons.append("already_purchased")
    if profile.exclude_course_ids is None:
        pass
    elif candidate.course_id in profile.exclude_course_ids:
        reasons.append("explicitly_excluded")
    if profile.exclude_enrolled_or_completed is not True:
        return
    for field_name, course_ids, reason in (
        ("enrolled_course_ids", profile.enrolled_course_ids, "already_enrolled"),
        ("completed_course_ids", profile.completed_course_ids, "already_completed"),
    ):
        if course_ids is None:
            warnings.add(f"profile.{field_name}")
        elif candidate.course_id in course_ids:
            reasons.append(reason)


def _apply_budget_filter(
    candidate: CourseCandidate,
    profile: StudentProfile,
    reasons: list[str],
    warnings: set[str],
) -> None:
    if profile.max_budget_amount is None:
        return
    if candidate.price_amount is None or candidate.price_currency is None:
        reasons.append("unknown_price")
        warnings.add(f"courses.{candidate.course_id}.price")
        return
    if candidate.price_currency.upper() != profile.budget_currency.upper():
        reasons.append("price_currency_mismatch")
        warnings.add(f"courses.{candidate.course_id}.price_currency")
        return
    if candidate.price_amount > profile.max_budget_amount:
        reasons.append("over_budget")


def _apply_time_filter(
    candidate: CourseCandidate,
    profile: StudentProfile,
    reasons: list[str],
    warnings: set[str],
) -> None:
    if profile.available_hours_per_week is None:
        return
    if candidate.required_hours_per_week is None:
        reasons.append("unknown_weekly_hours")
        warnings.add(f"courses.{candidate.course_id}.required_hours_per_week")
    elif candidate.required_hours_per_week > profile.available_hours_per_week:
        reasons.append("over_available_hours")


def _apply_prerequisite_filter(
    candidate: CourseCandidate,
    profile: StudentProfile,
    course_prerequisites: Mapping[str, Collection[str] | None] | None,
    reasons: list[str],
    warnings: set[str],
) -> None:
    if course_prerequisites is None or candidate.course_id not in course_prerequisites:
        reasons.append("unknown_course_prerequisites")
        warnings.add(f"course_prerequisites.{candidate.course_id}")
        return
    raw_prerequisites = course_prerequisites[candidate.course_id]
    if raw_prerequisites is None:
        reasons.append("unknown_course_prerequisites")
        warnings.add(f"course_prerequisites.{candidate.course_id}")
        return
    prerequisite_ids = _validate_string_collection(
        raw_prerequisites,
        field_name=f"course_prerequisites[{candidate.course_id}]",
    )
    if not prerequisite_ids:
        return
    if profile.completed_course_ids is None:
        reasons.append("unknown_completion_history")
        warnings.add("profile.completed_course_ids")
        return
    unmet = set(prerequisite_ids) - set(profile.completed_course_ids)
    if unmet:
        reasons.append("unmet_prerequisites")


def _validate_string_collection(
    values: Collection[str],
    *,
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes, bytearray)):
        raise ValueError(f"{field_name} must be a collection of strings")
    normalized = tuple(values)
    if any(not isinstance(value, str) or not value.strip() for value in normalized):
        raise ValueError(f"{field_name} must contain non-empty strings")
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _has_values(values: Collection[str] | None) -> bool:
    return values is not None and any(value.strip() for value in values)


def _is_currency(value: str) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z]{3}", value) is not None
