"""OpenAPI compatibility metadata for the MailChannels SDK."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .version import __version__

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ApiSpecCompatibility:
    """MailChannels OpenAPI document targeted by this SDK release."""

    source_url: str
    openapi_version: str
    sha256: str
    checked_at: str
    sdk_version: str

    def to_dict(self) -> dict[str, str]:
        """Return compatibility metadata as a plain dictionary."""
        logger.debug(
            "Serializing OpenAPI compatibility metadata for SDK %s.",
            self.sdk_version,
        )
        return {
            "source_url": self.source_url,
            "openapi_version": self.openapi_version,
            "sha256": self.sha256,
            "checked_at": self.checked_at,
            "sdk_version": self.sdk_version,
        }


API_SPEC_COMPATIBILITY = ApiSpecCompatibility(
    source_url="https://docs.mailchannels.com/email-api.yaml",
    openapi_version="1.7.0",
    sha256="98e341bf1d99061d959a506e2ac1956de2a67d18d79f496f2e770bb22956115b",
    checked_at="2026-08-18T00:27:23+00:00",
    sdk_version=__version__,
)
