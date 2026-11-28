"""Synchronous PostgreSQL connection for Celery tasks."""

import psycopg2
from psycopg2.extensions import connection as PostgresConnection

from src.core.config import settings


def connect_db() -> PostgresConnection:
    return psycopg2.connect(settings.DATABASE_URL.replace("+asyncpg", ""))
