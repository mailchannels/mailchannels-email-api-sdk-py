"""Shared URL path helpers for MailChannels resources."""

from __future__ import annotations

from urllib.parse import quote


def encode_path_segment(value: str | int) -> str:
    """Encode one URL path segment."""
    return quote(str(value), safe="")


def encode_path_segments(*segments: str | int) -> str:
    """Build an absolute URL path from encoded path segments."""
    return "/" + "/".join(encode_path_segment(segment) for segment in segments)
