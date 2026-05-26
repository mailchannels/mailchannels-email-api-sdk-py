"""OpenAPI compatibility metadata for the MailChannels SDK."""

from __future__ import annotations

import logging
from dataclasses import dataclass

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
    source_url="https://docs.mailchannels.net/email-api.yaml",
    openapi_version="0.21.1",
    sha256="55150d6ed81654a7135843c3bd70b1e661bc75a5fc7b2d1f1f44fbd607e90bff",
    checked_at="2026-05-14T00:00:00+00:00",
    sdk_version="0.1.2",
)
