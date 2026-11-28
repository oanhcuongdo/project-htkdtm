"""Semantic embedding ranker for immutable recommendation catalog versions."""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol, Sequence, TypeGuard

from src.recommendations.candidate_filter import (
    CandidateFilterResult,
    fallback_ordered_candidate_ids,
    resolve_candidate_course_ids,
    validate_filter_dataset_version,
)
from src.recommendations.tfidf_baseline import (
    CourseDocument,
    LearnerProfile,
    select_candidate_courses,
)


DEFAULT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_MODEL_REVISION = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
DEFAULT_BATCH_SIZE = 32
_CACHE_SCHEMA_VERSION = 2


class SentenceEncoder(Protocol):
    def encode(
        self,
        sentences: Sequence[str],
        *,
        batch_size: int,
        show_progress_bar: bool,
        convert_to_numpy: bool,
        normalize_embeddings: bool,
    ) -> object: ...


@dataclass(frozen=True)
class SemanticRankedCourse:
    course_id: str
    rank: int
    score: float | None


@dataclass(frozen=True)
class M1RecommendationResult:
    dataset_version_id: str
    model_version: str
    candidate_set_hash: str
    eligible_candidate_ids: tuple[str, ...]
    ranked_courses: tuple[SemanticRankedCourse, ...]
    fallback_reason: str | None
    missing_fields_warning: tuple[str, ...] = ()
    score_scale: str = "0-1"


class M1SemanticRanker:
    """Rank a shared, pre-filtered candidate set with normalized cosine.

    Course embeddings are cached as compressed JSON outside the repository by
    default. Call :meth:`precompute_catalog` when publishing a dataset version
    so requests do not pay the corpus-encoding cost.
    """

    def __init__(
        self,
        *,
        cache_dir: Path | None = None,
        model_name: str = DEFAULT_MODEL_NAME,
        model_revision: str = DEFAULT_MODEL_REVISION,
        encoder: SentenceEncoder | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        if not model_name.strip():
            raise ValueError("model_name must not be empty")
        if not model_revision.strip():
            raise ValueError("model_revision must not be empty")
        if batch_size < 1:
            raise ValueError("batch_size must be at least 1")

        configured_cache_dir = os.environ.get("AI_M1_CACHE_DIR")
        self.cache_dir = cache_dir or (
            Path(configured_cache_dir)
            if configured_cache_dir
            else Path.home() / ".cache" / "smartedu" / "m1"
        )
        self.model_name = model_name
        self.model_revision = model_revision
        self.model_version = f"{model_name}@{model_revision}"
        self.batch_size = batch_size
        self._encoder = encoder
        self._prepared: dict[
            str, tuple[str, dict[str, tuple[float, ...]]]
        ] = {}
        self._lock = threading.RLock()

    def precompute_catalog(
        self,
        dataset_version_id: str,
        courses: Sequence[CourseDocument],
    ) -> bool:
        """Create or validate the immutable cache; return whether it was reused."""
        version_id = _canonical_version_id(dataset_version_id)
        ordered_courses = sorted(courses, key=lambda course: course.course_id)
        course_ids = [course.course_id for course in ordered_courses]
        if not course_ids:
            raise ValueError("cannot precompute an empty course catalog")
        if len(course_ids) != len(set(course_ids)):
            raise ValueError("course document IDs must be unique")

        texts = [course.text for course in ordered_courses]
        catalog_hash = _catalog_hash(ordered_courses, texts)
        with self._lock:
            prepared = self._prepared.get(version_id)
            if prepared is not None:
                if prepared[0] != catalog_hash:
                    raise ValueError(
                        "catalog content changed without a new dataset version"
                    )
                return True

            cache_path = self._cache_path(version_id)
            if cache_path.exists():
                vectors = self._load_cache(
                    cache_path,
                    version_id=version_id,
                    catalog_hash=catalog_hash,
                    course_ids=course_ids,
                )
                self._prepared[version_id] = (catalog_hash, vectors)
                return True

            vectors = self._encode(texts)
            if len(vectors) != len(course_ids):
                raise ValueError("encoder returned a different number of course vectors")
            dimension = len(vectors[0])
            if any(len(vector) != dimension for vector in vectors):
                raise ValueError("encoder returned inconsistent vector dimensions")

            vector_index = dict(zip(course_ids, vectors))
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._write_cache(
                cache_path,
                {
                    "schema_version": _CACHE_SCHEMA_VERSION,
                    "dataset_version_id": version_id,
                    "model_version": self.model_version,
                    "catalog_hash": catalog_hash,
                    "course_ids": course_ids,
                    "dimension": dimension,
                    "vectors": [list(vector_index[course_id]) for course_id in course_ids],
                },
            )
            self._prepared[version_id] = (catalog_hash, vector_index)
            return False

    def rank(
        self,
        *,
        dataset_version_id: str,
        courses: Sequence[CourseDocument],
        profile: LearnerProfile,
        top_k: int = 5,
        candidate_filter_result: CandidateFilterResult | None = None,
    ) -> M1RecommendationResult:
        """Rank the caller's shared, pre-filtered candidate set."""
        _validate_request(profile, top_k)
        version_id = _canonical_version_id(dataset_version_id)
        validate_filter_dataset_version(candidate_filter_result, version_id)
        candidate_ids_from_filter = resolve_candidate_course_ids(
            profile.candidate_course_ids,
            candidate_filter_result,
        )
        candidates = select_candidate_courses(courses, candidate_ids_from_filter)
        candidate_ids = tuple(course.course_id for course in candidates)
        candidate_hash = hashlib.sha256(
            "\n".join(sorted(candidate_ids)).encode("utf-8")
        ).hexdigest()

        query = profile.query_text
        if not candidate_ids:
            return M1RecommendationResult(
                dataset_version_id=version_id,
                model_version=self.model_version,
                candidate_set_hash=candidate_hash,
                eligible_candidate_ids=candidate_ids,
                ranked_courses=(),
                fallback_reason="no_eligible_candidates",
                missing_fields_warning=(
                    candidate_filter_result.missing_fields_warning
                    if candidate_filter_result is not None
                    else ()
                ),
            )
        if not query:
            if candidate_filter_result is None:
                fallback = sorted(
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
                fallback = [
                    course_index[course_id] for course_id in fallback_ids[:top_k]
                ]
            return M1RecommendationResult(
                dataset_version_id=version_id,
                model_version=self.model_version,
                candidate_set_hash=candidate_hash,
                eligible_candidate_ids=candidate_ids,
                ranked_courses=tuple(
                    SemanticRankedCourse(
                        course_id=course.course_id, rank=index, score=None
                    )
                    for index, course in enumerate(fallback, start=1)
                ),
                fallback_reason="cold_start",
                missing_fields_warning=(
                    candidate_filter_result.missing_fields_warning
                    if candidate_filter_result is not None
                    else ()
                ),
            )

        self.precompute_catalog(version_id, courses)
        with self._lock:
            prepared = self._prepared[version_id][1]
            missing_ids = sorted(set(candidate_ids) - prepared.keys())
            if missing_ids:
                raise ValueError(
                    "candidate IDs are missing from the versioned catalog: "
                    + ", ".join(missing_ids)
                )
            query_vector = self._encode([f"Learner query: {query}"])[0]
            scored = [
                (
                    candidate_id,
                    _cosine(prepared[candidate_id], query_vector),
                )
                for candidate_id in candidate_ids
            ]

        scored.sort(key=lambda item: (-item[1], item[0]))
        ranked = tuple(
            SemanticRankedCourse(
                course_id=course_id,
                rank=index,
                score=round((cosine + 1.0) / 2.0, 8),
            )
            for index, (course_id, cosine) in enumerate(scored[:top_k], start=1)
        )
        return M1RecommendationResult(
            dataset_version_id=version_id,
            model_version=self.model_version,
            candidate_set_hash=candidate_hash,
            eligible_candidate_ids=candidate_ids,
            ranked_courses=ranked,
            fallback_reason=None,
            missing_fields_warning=(
                candidate_filter_result.missing_fields_warning
                if candidate_filter_result is not None
                else ()
            ),
        )

    def _get_encoder(self) -> SentenceEncoder:
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as error:
                raise RuntimeError(
                    "M1 requires sentence-transformers; install src/ai/requirements.txt"
                ) from error
            self._encoder = SentenceTransformer(
                self.model_name,
                revision=self.model_revision,
            )
        return self._encoder

    def _encode(self, texts: Sequence[str]) -> list[tuple[float, ...]]:
        encoded = self._get_encoder().encode(
            list(texts),
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        if hasattr(encoded, "tolist"):
            encoded = encoded.tolist()
        if not isinstance(encoded, list) or len(encoded) != len(texts):
            raise ValueError("encoder returned an invalid embedding batch")

        vectors: list[tuple[float, ...]] = []
        for raw_vector in encoded:
            if not isinstance(raw_vector, (list, tuple)) or not raw_vector:
                raise ValueError("encoder returned an empty or invalid embedding")
            vector = tuple(float(value) for value in raw_vector)
            if not all(math.isfinite(value) for value in vector):
                raise ValueError("encoder returned a non-finite embedding value")
            norm = math.sqrt(math.fsum(value * value for value in vector))
            if norm == 0:
                raise ValueError("encoder returned a zero-length embedding")
            vectors.append(tuple(value / norm for value in vector))
        return vectors

    def _cache_path(self, dataset_version_id: str) -> Path:
        key = hashlib.sha256(
            f"{_CACHE_SCHEMA_VERSION}\0{dataset_version_id}\0{self.model_version}".encode(
                "utf-8"
            )
        ).hexdigest()
        return self.cache_dir / f"{key}.json.gz"

    def _load_cache(
        self,
        cache_path: Path,
        *,
        version_id: str,
        catalog_hash: str,
        course_ids: Sequence[str],
    ) -> dict[str, tuple[float, ...]]:
        try:
            with gzip.open(cache_path, "rt", encoding="utf-8") as cache_file:
                payload: object = json.load(cache_file)
        except (OSError, EOFError, json.JSONDecodeError) as error:
            raise RuntimeError(f"unable to read M1 embedding cache {cache_path}") from error

        if not _is_json_object(payload):
            raise ValueError("M1 embedding cache must contain a JSON object")
        expected = {
            "schema_version": _CACHE_SCHEMA_VERSION,
            "dataset_version_id": version_id,
            "model_version": self.model_version,
            "catalog_hash": catalog_hash,
            "course_ids": list(course_ids),
        }
        for key, value in expected.items():
            if payload.get(key) != value:
                raise ValueError(
                    f"M1 embedding cache mismatch for {key}; publish a new dataset version"
                )

        raw_vectors = payload.get("vectors")
        dimension = payload.get("dimension")
        if (
            not isinstance(raw_vectors, list)
            or isinstance(dimension, bool)
            or not isinstance(dimension, int)
            or dimension < 1
            or len(raw_vectors) != len(course_ids)
        ):
            raise ValueError("M1 embedding cache has invalid vector metadata")

        vectors: dict[str, tuple[float, ...]] = {}
        for course_id, raw_vector in zip(course_ids, raw_vectors):
            if not isinstance(raw_vector, list) or len(raw_vector) != dimension:
                raise ValueError("M1 embedding cache has an invalid vector shape")
            vector = tuple(float(value) for value in raw_vector)
            if not all(math.isfinite(value) for value in vector):
                raise ValueError("M1 embedding cache contains non-finite values")
            norm = math.sqrt(math.fsum(value * value for value in vector))
            if not math.isclose(norm, 1.0, rel_tol=1e-4, abs_tol=1e-4):
                raise ValueError("M1 embedding cache contains an unnormalized vector")
            vectors[course_id] = vector
        return vectors

    @staticmethod
    def _write_cache(cache_path: Path, payload: Mapping[str, object]) -> None:
        with tempfile.NamedTemporaryFile(
            dir=cache_path.parent,
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
        try:
            with gzip.open(temporary_path, "wt", encoding="utf-8") as cache_file:
                json.dump(payload, cache_file, ensure_ascii=False, separators=(",", ":"))
            os.replace(temporary_path, cache_path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()


def _validate_request(profile: LearnerProfile, top_k: int) -> None:
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    if not profile.learner_key.strip():
        raise ValueError("learner_key must not be empty")


def _canonical_version_id(dataset_version_id: str) -> str:
    if not isinstance(dataset_version_id, str) or not dataset_version_id.strip():
        raise ValueError("dataset_version_id must be a non-empty string")
    return dataset_version_id.strip()


def _catalog_hash(
    courses: Sequence[CourseDocument],
    texts: Sequence[str],
) -> str:
    canonical_catalog = json.dumps(
        [
            [
                course.course_id,
                text,
                course.skill_ids,
                course.level,
            ]
            for course, text in zip(courses, texts)
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_catalog.encode("utf-8")).hexdigest()


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("query and course embedding dimensions do not match")
    similarity = math.fsum(a * b for a, b in zip(left, right))
    return max(-1.0, min(1.0, similarity))


def _is_json_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)
