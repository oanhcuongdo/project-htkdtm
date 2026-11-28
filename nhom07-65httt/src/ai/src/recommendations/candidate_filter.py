"""Deterministic hard-constraint filtering shared by recommendation models."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Collection, Mapping, Sequence


OFFER_TYPES = frozenset({"INTERNAL", "EXTERNAL_REFERENCE"})
DEFAULT_FALLBACK_LIMIT = 5


def _decimal_value(value: Decimal | int | float, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a non-negative number")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"{field_name} must be a non-negative number") from error
    if not result.is_finite() or result < 0:
        raise ValueError(f"{field_name} must be a finite non-negative number")
    return result


def _optional_decimal(
    value: Decimal | int | float | None, field_name: str
) -> Decimal | None:
    if value is None:
        return None
    return _decimal_value(value, field_name)


@dataclass(frozen=True)
class CourseCandidate:
    """Normalized course data needed by filtering and safe fallback ranking."""

    course_id: str
    approval_status: str | None = None
    offer_type: str | None = None
    price_amount: Decimal | int | float | None = None
    price_currency: str | None = None
    required_hours_per_week: Decimal | int | float | None = None
    popularity_score: Decimal | int | float | None = None

    def __post_init__(self) -> None:
        if not self.course_id or not self.course_id.strip():
            raise ValueError("course_id must not be empty")
        object.__setattr__(
            self, "price_amount", _optional_decimal(self.price_amount, "price_amount")
        )
        object.__setattr__(
            self,
            "required_hours_per_week",
            _optional_decimal(self.required_hours_per_week, "required_hours_per_week"),
        )
        object.__setattr__(
            self,
            "popularity_score",
            _optional_decimal(self.popularity_score, "popularity_score"),
        )
        if self.price_currency is not None:
            currency = self.price_currency.strip().upper()
            if len(currency) != 3 or not currency.isalpha():
                raise ValueError("price_currency must be a three-letter currency code")
            object.__setattr__(self, "price_currency", currency)


@dataclass(frozen=True)
class StudentProfile:
    """Filter-relevant profile fields; ``None`` means unknown, not zero/empty."""

    max_budget_amount: Decimal | int | float | None = None
    budget_currency: str | None = None
    available_hours_per_week: Decimal | int | float | None = None
    goals: Collection[str] | None = None
    current_skills: Collection[str] | None = None
    target_level: str | None = None
    purchased_course_ids: frozenset[str] | None = None
    enrolled_course_ids: frozenset[str] | None = None
    completed_course_ids: frozenset[str] | None = None
    allowed_offer_types: frozenset[str] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "max_budget_amount",
            _optional_decimal(self.max_budget_amount, "max_budget_amount"),
        )
        object.__setattr__(
            self,
            "available_hours_per_week",
            _optional_decimal(
                self.available_hours_per_week, "available_hours_per_week"
            ),
        )
        if self.budget_currency is not None:
            currency = self.budget_currency.strip().upper()
            if len(currency) != 3 or not currency.isalpha():
                raise ValueError("budget_currency must be a three-letter currency code")
            object.__setattr__(self, "budget_currency", currency)
        if self.allowed_offer_types is not None:
            offer_types = frozenset(value.upper() for value in self.allowed_offer_types)
            invalid_types = offer_types - OFFER_TYPES
            if invalid_types:
                raise ValueError(
                    "allowed_offer_types contains unsupported values: "
                    + ", ".join(sorted(invalid_types))
                )
            object.__setattr__(self, "allowed_offer_types", offer_types)


@dataclass(frozen=True)
class RejectedCandidate:
    course_id: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class CandidateFilterResult:
    """Eligible candidates and a constraint-safe popularity fallback pool."""

    candidates: tuple[CourseCandidate, ...]
    fallback_candidates: tuple[CourseCandidate, ...]
    missing_fields_warning: tuple[str, ...]
    candidate_warnings: Mapping[str, tuple[str, ...]]
    rejected_candidates: tuple[RejectedCandidate, ...]
    is_cold_start: bool
    fallback_reason: str | None


def filter_candidates(
    candidates: Sequence[CourseCandidate],
    profile: StudentProfile,
    course_prerequisites: Mapping[str, Collection[str] | None],
    *,
    fallback_limit: int = DEFAULT_FALLBACK_LIMIT,
) -> CandidateFilterResult:
    """Apply shared hard filters and prepare a safe popularity fallback.

    ``course_prerequisites`` must contain an entry for every candidate. An empty
    collection means the course has no prerequisites; a missing key or ``None``
    means prerequisite data is unknown and the course is excluded. This prevents
    incomplete prerequisite data from silently bypassing the hard constraint.

    Weekly availability is compared only with an explicit
    ``required_hours_per_week`` estimate. Total ``duration_minutes`` is not
    treated as weekly workload. If the learner did not provide a budget or
    weekly availability, that filter is skipped and reported in
    ``missing_fields_warning``.
    """
    if fallback_limit < 1:
        raise ValueError("fallback_limit must be at least 1")

    candidate_ids = [candidate.course_id for candidate in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("candidate course_id values must be unique")

    missing_fields = _missing_profile_fields(profile)
    is_cold_start = (
        not profile.goals and not profile.current_skills and profile.target_level is None
    )
    if is_cold_start:
        missing_fields.append("personalization_signals")

    allowed_offer_types = (
        profile.allowed_offer_types
        if profile.allowed_offer_types is not None
        else OFFER_TYPES
    )
    excluded_course_ids = set()
    for course_ids in (
        profile.purchased_course_ids,
        profile.enrolled_course_ids,
        profile.completed_course_ids,
    ):
        if course_ids is not None:
            excluded_course_ids.update(course_ids)

    eligible: list[CourseCandidate] = []
    rejected: list[RejectedCandidate] = []
    candidate_warnings: dict[str, tuple[str, ...]] = {}

    for candidate in candidates:
        reasons: list[str] = []
        if candidate.approval_status != "approved":
            reasons.append("not_approved")
        if candidate.offer_type not in allowed_offer_types:
            reasons.append("offer_type_not_allowed")
        if candidate.course_id in excluded_course_ids:
            reasons.append("already_purchased_enrolled_or_completed")

        if profile.max_budget_amount is not None and profile.budget_currency is not None:
            if candidate.price_amount is None:
                reasons.append("price_unknown")
            elif candidate.price_currency is None:
                reasons.append("price_currency_unknown")
            elif candidate.price_currency != profile.budget_currency:
                reasons.append("currency_mismatch")
            elif candidate.price_amount > profile.max_budget_amount:
                reasons.append("over_budget")

        if profile.available_hours_per_week is not None:
            if candidate.required_hours_per_week is None:
                reasons.append("weekly_workload_unknown")
            elif candidate.required_hours_per_week > profile.available_hours_per_week:
                reasons.append("weekly_workload_exceeds_availability")

        if candidate.course_id not in course_prerequisites:
            reasons.append("prerequisite_data_unknown")
        else:
            prerequisite_ids = course_prerequisites[candidate.course_id]
            if prerequisite_ids is None:
                reasons.append("prerequisite_data_unknown")
            elif prerequisite_ids:
                if profile.completed_course_ids is None:
                    reasons.append("completed_course_history_unknown")
                else:
                    unmet = sorted(set(prerequisite_ids) - profile.completed_course_ids)
                    if unmet:
                        reasons.extend(f"prerequisite_not_completed:{item}" for item in unmet)

        if reasons:
            rejected.append(
                RejectedCandidate(course_id=candidate.course_id, reasons=tuple(reasons))
            )
            continue

        eligible.append(candidate)
        candidate_warnings[candidate.course_id] = tuple(missing_fields)

    eligible.sort(key=lambda candidate: candidate.course_id)
    fallback_candidates = sorted(
        eligible,
        key=lambda candidate: (
            candidate.popularity_score is None,
            -(candidate.popularity_score or Decimal(0)),
            candidate.course_id,
        ),
    )[:fallback_limit]

    if any(candidate.popularity_score is None for candidate in fallback_candidates):
        missing_fields.append("popularity_score")
        for candidate in fallback_candidates:
            if candidate.popularity_score is None:
                candidate_warnings[candidate.course_id] = tuple(missing_fields)

    fallback_reason = (
        "no_eligible_candidates"
        if not eligible
        else "cold_start"
        if is_cold_start
        else None
    )
    if fallback_reason == "no_eligible_candidates":
        missing_fields.append("no_eligible_candidates")

    return CandidateFilterResult(
        candidates=tuple(eligible),
        fallback_candidates=tuple(fallback_candidates),
        missing_fields_warning=tuple(dict.fromkeys(missing_fields)),
        candidate_warnings=candidate_warnings,
        rejected_candidates=tuple(rejected),
        is_cold_start=is_cold_start,
        fallback_reason=fallback_reason,
    )


def _missing_profile_fields(profile: StudentProfile) -> list[str]:
    missing: list[str] = []
    if profile.max_budget_amount is None:
        missing.append("max_budget_amount")
    elif profile.budget_currency is None:
        missing.append("budget_currency")
    if profile.available_hours_per_week is None:
        missing.append("available_hours_per_week")
    if profile.purchased_course_ids is None:
        missing.append("purchased_course_ids")
    if profile.enrolled_course_ids is None:
        missing.append("enrolled_course_ids")
    if profile.completed_course_ids is None:
        missing.append("completed_course_ids")
    if profile.goals is None:
        missing.append("goals")
    if profile.current_skills is None:
        missing.append("current_skills")
    if profile.target_level is None:
        missing.append("target_level")
    return missing
