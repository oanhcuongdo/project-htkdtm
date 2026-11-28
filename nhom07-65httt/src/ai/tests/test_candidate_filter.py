from decimal import Decimal

import pytest

from src.recommendations.candidate_filter import (
    CourseCandidate,
    StudentProfile,
    filter_candidates,
)


def candidate(
    course_id: str,
    *,
    price: int | None = 100,
    weekly_hours: int | None = 4,
    popularity: int | None = 0,
    offer_type: str = "INTERNAL",
    approval_status: str = "approved",
) -> CourseCandidate:
    return CourseCandidate(
        course_id=course_id,
        approval_status=approval_status,
        offer_type=offer_type,
        price_amount=price,
        price_currency="VND" if price is not None else None,
        required_hours_per_week=weekly_hours,
        popularity_score=popularity,
    )


def complete_profile(
    *,
    purchased_course_ids: frozenset[str] | None = frozenset(),
    enrolled_course_ids: frozenset[str] | None = frozenset(),
    completed_course_ids: frozenset[str] | None = frozenset(),
    allowed_offer_types: frozenset[str] | None = None,
) -> StudentProfile:
    return StudentProfile(
        max_budget_amount=500,
        budget_currency="VND",
        available_hours_per_week=5,
        goals=("data analyst",),
        current_skills=("sql",),
        target_level="BEGINNER",
        purchased_course_ids=purchased_course_ids,
        enrolled_course_ids=enrolled_course_ids,
        completed_course_ids=completed_course_ids,
        allowed_offer_types=allowed_offer_types,
    )


def test_filters_unapproved_wrong_type_owned_over_budget_and_overload():
    candidates = [
        candidate("eligible"),
        candidate("draft", approval_status="pending_review"),
        candidate("external", offer_type="EXTERNAL_REFERENCE"),
        candidate("owned"),
        candidate("enrolled"),
        candidate("done"),
        candidate("expensive", price=900),
        candidate("overloaded", weekly_hours=8),
    ]
    profile = complete_profile(
        purchased_course_ids=frozenset({"owned"}),
        enrolled_course_ids=frozenset({"enrolled"}),
        completed_course_ids=frozenset({"done"}),
        allowed_offer_types=frozenset({"INTERNAL"}),
    )

    result = filter_candidates(
        candidates,
        profile,
        {item.course_id: frozenset() for item in candidates},
    )

    assert [item.course_id for item in result.candidates] == ["eligible"]
    reasons = {item.course_id: item.reasons for item in result.rejected_candidates}
    assert reasons["draft"] == ("not_approved",)
    assert reasons["external"] == ("offer_type_not_allowed",)
    assert reasons["owned"] == ("already_purchased_enrolled_or_completed",)
    assert reasons["enrolled"] == ("already_purchased_enrolled_or_completed",)
    assert reasons["done"] == ("already_purchased_enrolled_or_completed",)
    assert reasons["expensive"] == ("over_budget",)
    assert reasons["overloaded"] == ("weekly_workload_exceeds_availability",)


def test_prerequisites_require_completed_course_and_never_relax_on_fallback():
    candidates = [candidate("advanced"), candidate("beginner")]
    profile = complete_profile(completed_course_ids=frozenset({"intro"}))

    result = filter_candidates(
        candidates,
        profile,
        {
            "advanced": frozenset({"intro"}),
            "beginner": frozenset(),
        },
    )

    assert [item.course_id for item in result.candidates] == ["advanced", "beginner"]
    assert all(
        prerequisite_id in profile.completed_course_ids
        for course_id in ("advanced", "beginner")
        for prerequisite_id in {
            "advanced": frozenset({"intro"}),
            "beginner": frozenset(),
        }[course_id]
    )


@pytest.mark.parametrize(
    ("prerequisite_index", "completed_course_ids", "expected_reason"),
    [
        ({}, frozenset(), "prerequisite_data_unknown"),
        ({"advanced": None}, frozenset(), "prerequisite_data_unknown"),
        (
            {"advanced": frozenset({"intro"})},
            frozenset(),
            "prerequisite_not_completed:intro",
        ),
        (
            {"advanced": frozenset({"intro"})},
            None,
            "completed_course_history_unknown",
        ),
    ],
)
def test_unknown_or_unmet_prerequisites_fail_closed(
    prerequisite_index: dict[str, frozenset[str] | None],
    completed_course_ids: frozenset[str] | None,
    expected_reason: str,
):
    profile = complete_profile(completed_course_ids=completed_course_ids)

    result = filter_candidates(
        [candidate("advanced")],
        profile,
        prerequisite_index,
    )

    assert result.candidates == ()
    assert expected_reason in result.rejected_candidates[0].reasons
    assert result.fallback_candidates == ()
    assert result.fallback_reason == "no_eligible_candidates"


def test_missing_profile_filters_keep_candidates_and_flag_cold_start_fallback():
    candidates = [
        candidate("popular", popularity=10),
        candidate("less-popular", popularity=2),
        candidate("unapproved-popular", approval_status="pending_review", popularity=100),
    ]
    profile = StudentProfile(
        purchased_course_ids=frozenset(),
        enrolled_course_ids=frozenset(),
        completed_course_ids=frozenset(),
    )

    result = filter_candidates(
        candidates,
        profile,
        {item.course_id: frozenset() for item in candidates},
        fallback_limit=1,
    )

    assert {item.course_id for item in result.candidates} == {
        "popular",
        "less-popular",
    }
    assert [item.course_id for item in result.fallback_candidates] == ["popular"]
    assert result.is_cold_start is True
    assert result.fallback_reason == "cold_start"
    assert "max_budget_amount" in result.missing_fields_warning
    assert "available_hours_per_week" in result.missing_fields_warning
    assert "personalization_signals" in result.missing_fields_warning
    assert result.candidate_warnings["popular"] == result.missing_fields_warning
    assert "unapproved-popular" not in {
        item.course_id for item in result.fallback_candidates
    }


def test_candidate_set_is_independent_of_input_order():
    candidates = [candidate("z-course"), candidate("a-course")]
    profile = complete_profile()
    prerequisites = {item.course_id: frozenset() for item in candidates}

    forward = filter_candidates(candidates, profile, prerequisites)
    reversed_result = filter_candidates(list(reversed(candidates)), profile, prerequisites)

    assert [item.course_id for item in forward.candidates] == ["a-course", "z-course"]
    assert [item.course_id for item in forward.candidates] == [
        item.course_id for item in reversed_result.candidates
    ]


def test_known_budget_and_time_fail_closed_for_unknown_course_values():
    candidates = [
        candidate("unknown-price", price=None),
        candidate("unknown-workload", weekly_hours=None),
    ]

    result = filter_candidates(
        candidates,
        complete_profile(),
        {item.course_id: frozenset() for item in candidates},
    )

    assert result.candidates == ()
    reasons = {item.course_id: item.reasons for item in result.rejected_candidates}
    assert reasons["unknown-price"] == ("price_unknown",)
    assert reasons["unknown-workload"] == ("weekly_workload_unknown",)


def test_currency_mismatch_is_not_silently_converted():
    course = CourseCandidate(
        course_id="usd-course",
        approval_status="approved",
        offer_type="INTERNAL",
        price_amount=Decimal("10"),
        price_currency="USD",
        required_hours_per_week=2,
    )

    result = filter_candidates(
        [course],
        complete_profile(),
        {"usd-course": frozenset()},
    )

    assert result.candidates == ()
    assert result.rejected_candidates[0].reasons == ("currency_mismatch",)


def test_rejects_duplicate_candidate_ids_and_invalid_fallback_limit():
    profile = complete_profile()
    duplicate = candidate("same")

    with pytest.raises(ValueError, match="must be unique"):
        filter_candidates(
            [duplicate, duplicate],
            profile,
            {"same": frozenset()},
        )

    with pytest.raises(ValueError, match="at least 1"):
        filter_candidates(
            [candidate("one")],
            profile,
            {"one": frozenset()},
            fallback_limit=0,
        )
