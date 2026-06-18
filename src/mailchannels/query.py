"""Shared query-parameter helpers for MailChannels resources."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any
from urllib.parse import quote

logger = logging.getLogger(__name__)


def compact_query(values: dict[str, Any]) -> dict[str, Any]:
    """Remove unset query values and serialize supported Python values."""
    query = {
        key: serialize_query_value(value)
        for key, value in values.items()
        if value is not None
    }
    logger.debug("Built MailChannels query params keys=%s", sorted(query))
    return query


def encode_path_segment(value: str | int) -> str:
    """Encode one user-supplied URL path segment.

    Prefer a resource-local path helper when several methods share the same
    base path or combine multiple variables. Inline this helper when a route has
    just one variable and the path remains obvious.
    """
    return quote(str(value), safe="")


def pagination_query(
    *,
    limit: int | None = None,
    offset: int | None = None,
    **filters: Any,
) -> dict[str, Any]:
    """Build a compact query with common pagination parameters."""
    return compact_query({**filters, "limit": limit, "offset": offset})


def serialize_query_value(value: Any) -> Any:
    """Serialize a Python value into an HTTP query-parameter value."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return value
