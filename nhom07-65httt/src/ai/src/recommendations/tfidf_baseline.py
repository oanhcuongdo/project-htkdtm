"""Deterministic M0 course ranking with TF-IDF cosine similarity."""

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.recommendations.candidate_filter import (
    CandidateFilterResult,
    fallback_ordered_candidate_ids,
    resolve_candidate_course_ids,
    validate_filter_dataset_version,
)


MODEL_VERSION = "m0-tfidf-v1"
VECTORIZER_CONFIG = {
    "analyzer": "word",
    "lowercase": True,
    "ngram_range": [1, 2],
    "norm": "l2",
    "smooth_idf": True,
    "sublinear_tf": True,
    "token_pattern": r"(?u)\b\w+\b",
    "use_idf": True,
}


@dataclass(frozen=True)
class CourseDocument:
    course_id: str
    title: str
    description: str | None = None
    skills: tuple[str, ...] = ()
    direct_skills: tuple[str, ...] = ()
    inferred_skills: tuple[str, ...] = ()
    popularity_score: float | None = None
    skill_ids: tuple[str, ...] | None = None
    level: str | None = None

    def __post_init__(self) -> None:
        if not self.course_id.strip():
            raise ValueError("course_id must not be empty")
        if not self.title.strip():
            raise ValueError(f"title must not be empty for course {self.course_id}")
        if self.popularity_score is not None and (
            not math.isfinite(self.popularity_score) or self.popularity_score < 0
        ):
            raise ValueError("popularity_score must be finite and non-negative")

    @property
    def text(self) -> str:
        return " ".join(
            value.strip()
            for value in (
                self.title,
                self.description or "",
                *self.skills,
                *self.direct_skills,
                *self.inferred_skills,
            )
            if value and value.strip()
        )


@dataclass(frozen=True)
class LearnerProfile:
    learner_key: str
    goals: tuple[str, ...] = ()
    current_skills: tuple[str, ...] = ()
    target_text: str | None = None
    candidate_course_ids: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if not self.learner_key.strip():
            raise ValueError("learner_key must not be empty")
        if self.candidate_course_ids is not None and len(
            self.candidate_course_ids
        ) != len(set(self.candidate_course_ids)):
            raise ValueError(
                f"candidate_course_ids must be unique for learner {self.learner_key}"
            )

    @property
    def query_text(self) -> str:
        return " ".join(
            value.strip()
            for value in (*self.goals, *self.current_skills, self.target_text or "")
            if value and value.strip()
        )


@dataclass(frozen=True)
class RankedCourse:
    course: CourseDocument
    rank: int
    score: float
    ranking_method: str
    fallback_reason: str | None = None


class TfidfBaseline:
    """Fit once per released course snapshot and rank each test profile."""

    def __init__(
        self,
        courses: Sequence[CourseDocument],
        *,
        dataset_version_id: str | None = None,
    ) -> None:
        if not courses:
            raise ValueError("courses must contain at least one course")
        if dataset_version_id is not None and (
            not isinstance(dataset_version_id, str) or not dataset_version_id.strip()
        ):
            raise ValueError("dataset_version_id must be a non-empty string or null")
        self.dataset_version_id = (
            dataset_version_id.strip() if dataset_version_id is not None else None
        )
        course_ids = [course.course_id for course in courses]
        if len(course_ids) != len(set(course_ids)):
            raise ValueError("course_id values must be unique")

        self.courses = tuple(sorted(courses, key=lambda course: course.course_id))
        self.course_index = {
            course.course_id: index for index, course in enumerate(self.courses)
        }
        config = dict(VECTORIZER_CONFIG)
        config["ngram_range"] = tuple(config["ngram_range"])
        self.vectorizer = TfidfVectorizer(**config)
        try:
            self.course_matrix = self.vectorizer.fit_transform(
                [course.text for course in self.courses]
            )
        except ValueError as error:
            if "empty vocabulary" in str(error):
                raise ValueError(
                    "course catalog contains no indexable title, description, or skills"
                ) from error
            raise

    def rank(
        self,
        profile: LearnerProfile,
        *,
        top_k: int = 5,
        candidate_filter_result: CandidateFilterResult | None = None,
    ) -> tuple[RankedCourse, ...]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        if candidate_filter_result is not None:
            if self.dataset_version_id is None:
                raise ValueError(
                    "dataset_version_id is required when using candidate_filter_result"
                )
            validate_filter_dataset_version(
                candidate_filter_result,
                self.dataset_version_id,
            )

        candidate_ids = resolve_candidate_course_ids(
            profile.candidate_course_ids,
            candidate_filter_result,
        )
        candidates = select_candidate_courses(self.courses, candidate_ids)

        if not candidates:
            return ()

        candidate_indices = [self.course_index[course.course_id] for course in candidates]
        query = self.vectorizer.transform([profile.query_text])
        similarities = cosine_similarity(
            query, self.course_matrix[candidate_indices]
        ).ravel()

        if query.nnz == 0 or not similarities.any():
            reason = (
                "cold_start"
                if not profile.query_text
                else "no_tfidf_match"
            )
            if candidate_filter_result is None:
                fallback_courses = sorted(
                    candidates,
                    key=lambda course: (
                        course.popularity_score is None,
                        -(course.popularity_score or 0.0),
                        course.course_id,
                    ),
                )[:top_k]
            else:
                course_index = {
                    course.course_id: course for course in candidates
                }
                fallback_ids = fallback_ordered_candidate_ids(
                    candidate_filter_result,
                    tuple(course_index),
                )
                fallback_courses = [
                    course_index[course_id] for course_id in fallback_ids[:top_k]
                ]
            return tuple(
                RankedCourse(
                    course=course,
                    rank=rank,
                    score=0.0,
                    ranking_method="popularity_fallback",
                    fallback_reason=reason,
                )
                for rank, course in enumerate(fallback_courses, start=1)
            )

        scored_courses = sorted(
            zip(candidates, similarities),
            key=lambda item: (-float(item[1]), item[0].course_id),
        )[:top_k]
        return tuple(
            RankedCourse(
                course=course,
                rank=rank,
                score=min(1.0, max(0.0, float(score))),
                ranking_method="tfidf_cosine",
            )
            for rank, (course, score) in enumerate(scored_courses, start=1)
        )


def select_candidate_courses(
    courses: Sequence[CourseDocument],
    candidate_course_ids: Sequence[str] | None,
) -> tuple[CourseDocument, ...]:
    """Resolve the caller's shared, pre-filtered candidate IDs deterministically."""
    course_index = {course.course_id: course for course in courses}
    if len(course_index) != len(courses):
        raise ValueError("course_id values must be unique")
    if candidate_course_ids is None:
        selected_ids = sorted(course_index)
    else:
        if len(candidate_course_ids) != len(set(candidate_course_ids)):
            raise ValueError("candidate_course_ids must be unique")
        unknown_ids = set(candidate_course_ids) - course_index.keys()
        if unknown_ids:
            raise ValueError(
                "candidate_course_ids contain unknown courses: "
                + ", ".join(sorted(unknown_ids))
            )
        selected_ids = sorted(candidate_course_ids)
    return tuple(course_index[course_id] for course_id in selected_ids)


def terms_from_value(value: object, *, field_name: str) -> tuple[str, ...]:
    """Read text labels from strings or skill/goal objects in the data contract."""
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        raise ValueError(f"{field_name} must be a string, list, or null")

    terms: list[str] = []
    for item in value:
        if isinstance(item, str):
            term = item.strip()
        elif isinstance(item, Mapping):
            term = next(
                (
                    str(item[key]).strip()
                    for key in (
                        "label",
                        "name",
                        "skill_name",
                        "goal_name",
                        "skill_id",
                        "goal_id",
                        "id",
                    )
                    if item.get(key) is not None and str(item[key]).strip()
                ),
                "",
            )
        else:
            raise ValueError(f"{field_name} items must be strings or objects")
        if term:
            terms.append(term)
    return tuple(terms)
