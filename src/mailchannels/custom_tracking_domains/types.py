"""Custom tracking domain request and response types."""

from __future__ import annotations

import logging
from typing import Literal, TypedDict

from pydantic import BaseModel, ConfigDict, model_validator

logger = logging.getLogger(__name__)

CustomTrackingScope = Literal["click", "open", "unsubscribe"]
CustomTrackingStatus = Literal["active", "disabled"]


class CustomTrackingDomainListParams(TypedDict, total=False):
    """Query parameters for retrieving custom tracking domains."""

    name: str
    status: CustomTrackingStatus
    scope: CustomTrackingScope
    limit: int
    offset: int


class CustomTrackingDomain(BaseModel):
    """A registered MailChannels custom tracking domain."""

    model_config = ConfigDict(extra="allow")

    name: str
    hostname: str
    scope: CustomTrackingScope
    status: CustomTrackingStatus
    created_at: str


class CustomTrackingDomainListResponse(BaseModel):
    """Response model for listing custom tracking domains."""

    model_config = ConfigDict(extra="allow")

    custom_tracking_domains: list[CustomTrackingDomain]
    total: int


class CustomTrackingDomainResult(BaseModel):
    """Response model for registering or updating a custom tracking domain.

    MailChannels returns either a fully-registered `CustomTrackingDomain`
    (201/200) or a `DnsSetupRequired` pending-verification result (202) —
    both are success statuses, so both flow through this one model rather
    than needing status-code-aware response dispatch.
    """

    model_config = ConfigDict(extra="allow")

    name: str | None = None
    hostname: str | None = None
    scope: CustomTrackingScope | None = None
    status: CustomTrackingStatus | None = None
    created_at: str | None = None
    instructions: str | None = None
    token: str | None = None
    txt_record_name: str | None = None
    txt_record_value: str | None = None

    @model_validator(mode="after")
    def _validate_result_variant(self) -> CustomTrackingDomainResult:
        """Require either a registered domain or pending DNS setup result."""
        is_registered = (
            self.name is not None
            and self.hostname is not None
            and self.scope is not None
            and self.status is not None
            and self.created_at is not None
        )
        is_pending = (
            self.instructions is not None
            or self.token is not None
            or self.txt_record_name is not None
            or self.txt_record_value is not None
        )
        if not is_registered and not is_pending:
            logger.error(
                "MailChannels custom tracking domain response matched neither the "
                "registered nor pending DNS setup shape"
            )
            raise ValueError(
                "response must be a registered domain or a pending DNS setup result"
            )
        return self
