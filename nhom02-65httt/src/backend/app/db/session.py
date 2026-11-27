"""SQLAlchemy engine, SessionLocal factory, and FastAPI DB dependency."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def _create_db_engine() -> Engine:
    settings = get_settings()
    kwargs: dict[str, Any] = {"pool_pre_ping": True}
    if settings.DATABASE_URL.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(settings.DATABASE_URL, **kwargs)


engine = _create_db_engine()
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Yield a scoped SQLAlchemy session and close it after request handling."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
