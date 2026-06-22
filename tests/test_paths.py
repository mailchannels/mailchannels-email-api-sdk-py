"""Tests for shared URL path helpers."""

from __future__ import annotations

from mailchannels.paths import encode_path_segment, encode_path_segments


def test_encode_path_segment_escapes_reserved_characters() -> None:
    """It encodes user-supplied values as a single URL path segment."""
    assert encode_path_segment("a/b?c=d#e f%g") == "a%2Fb%3Fc%3Dd%23e%20f%25g"


def test_encode_path_segments_builds_absolute_path() -> None:
    """It builds a path from encoded static and user-supplied segments."""
    assert (
        encode_path_segments("sub-account", "client/a", "api-key", "key #1")
        == "/sub-account/client%2Fa/api-key/key%20%231"
    )
