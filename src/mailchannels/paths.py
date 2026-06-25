"""Shared URL path helpers for MailChannels resources."""

from __future__ import annotations

import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)


def encode_path_segment(value: str | int) -> str:
    """Encode one URL path segment."""
    return quote(str(value), safe="")


def encode_path_segments(*segments: str | int) -> str:
    """Build an absolute URL path from encoded path segments."""
    path = "/" + "/".join(encode_path_segment(segment) for segment in segments)
    logger.debug("Built MailChannels URL path segments=%s path=%s", len(segments), path)
    return path
