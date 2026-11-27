"""Compare literal JSON defaults without PostgreSQL's unsupported JSON equality operator."""

import json
import re

from sqlalchemy import JSON

_UNSUPPORTED = object()
_JSON_LITERAL = re.compile(
    r"^\(?\s*'((?:''|[^'])*)'\s*(?:::\s*(?:pg_catalog\.)?jsonb?)?\s*\)?$",
    re.IGNORECASE | re.DOTALL,
)


def _json_signature(rendered):
    if not isinstance(rendered, str):
        return _UNSUPPORTED
    match = _JSON_LITERAL.fullmatch(rendered.strip())
    if not match:
        return _UNSUPPORTED
    try:
        value = json.loads(match.group(1).replace("''", "'"))
    except json.JSONDecodeError:
        return _UNSUPPORTED
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compare_server_default(
    context,
    _inspected_column,
    metadata_column,
    inspected_default,
    _metadata_default,
    rendered_metadata_default,
):
    """Handle JSON literals used by this schema; defer other types to Alembic."""
    if context.dialect.name != "postgresql" or not isinstance(metadata_column.type, JSON):
        return None
    if inspected_default is None or rendered_metadata_default is None:
        return inspected_default != rendered_metadata_default
    actual = _json_signature(inspected_default)
    expected = _json_signature(rendered_metadata_default)
    if actual is _UNSUPPORTED or expected is _UNSUPPORTED:
        return None
    return actual != expected
