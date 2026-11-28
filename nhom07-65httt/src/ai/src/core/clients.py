"""Third-party client singletons for AI service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.core.config import settings

if TYPE_CHECKING:
    from qdrant_client import QdrantClient

_qdrant_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """Retrieve the QdrantClient singleton."""
    from qdrant_client import QdrantClient

    global _qdrant_client
    if _qdrant_client is None:
        if settings.QDRANT_URL:
            _qdrant_client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )
        else:
            _qdrant_client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
            )
    return _qdrant_client
