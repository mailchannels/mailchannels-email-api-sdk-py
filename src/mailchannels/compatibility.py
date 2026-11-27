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
    openapi_version="1.9.0",
    sha256="d87a3eae5cd7e9f5874f59da068e58a32d296a31aaa36bf6b6af4e0fd9aeb44d",
    checked_at="2026-11-25T20:22:00+00:00",
    sdk_version=__version__,
)
