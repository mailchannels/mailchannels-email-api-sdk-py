"""Email request and response types."""

from __future__ import annotations

import base64
import logging
import mimetypes
from datetime import datetime
from typing import Any, Literal, TypedDict

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from typing_extensions import NotRequired

logger = logging.getLogger(__name__)

UNSUBSCRIBE_URL_PLACEHOLDER = "{{mc-unsubscribe-url}}"
EmailHeaders = dict[str, str]
RESERVED_EMAIL_HEADERS = frozenset(
    {
        "authentication-results",
        "bcc",
        "cc",
        "content-transfer-encoding",
        "content-type",
        "dkim-signature",
        "from",
        "message-id",
        "received",
        "reply-to",
        "subject",
        "to",
    }
)


class EmailAddressDict(TypedDict, total=False):
    """Dictionary form of a MailChannels email address."""

    email: str
    name: str


class ContentDict(TypedDict, total=False):
    """Dictionary form of a MailChannels content part."""

    type: str
    value: str
    template_type: Literal["mustache"]


class AttachmentDict(TypedDict, total=False):
    """Dictionary form of a MailChannels attachment."""

    content: str
    filename: str
    type: str
    disposition: str
    content_id: str


class TrackingToggleDict(TypedDict, total=False):
    """Dictionary form of an open/click tracking toggle."""

    enable: bool
    custom_domain_name: str


class TrackingSettingsDict(TypedDict, total=False):
    """Dictionary form of MailChannels tracking settings."""

    open_tracking: TrackingToggleDict
    click_tracking: TrackingToggleDict


class UnsubscribeSettingsDict(TypedDict, total=False):
    """Dictionary form of MailChannels unsubscribe settings."""

    custom_domain_name: str


class PersonalizationDict(TypedDict, total=False):
    """Dictionary form of a MailChannels personalization."""

    to: list[EmailAddressDict]
    cc: NotRequired[list[EmailAddressDict]]
    bcc: NotRequired[list[EmailAddressDict]]
    subject: NotRequired[str]
    from_: NotRequired[EmailAddressDict]
    reply_to: NotRequired[EmailAddressDict]
    envelope_from: NotRequired[EmailAddressDict]
    headers: NotRequired[EmailHeaders]
    substitutions: NotRequired[dict[str, str]]
    dynamic_template_data: NotRequired[dict[str, Any]]
    dkim_domain: NotRequired[str]
    dkim_private_key: NotRequired[str]
    dkim_selector: NotRequired[str]


class SendParams(TypedDict, total=False):
    """Resend-style or MailChannels-style email parameters."""

    from_: EmailAddressDict
    from_email: EmailAddressDict
    from_address: EmailAddressDict
    from_field: EmailAddressDict
    from_name: str
    from_display_name: str
    subject: str
    personalizations: list[PersonalizationDict]
    to: list[EmailAddressDict] | EmailAddressDict | list[str] | str
    cc: list[EmailAddressDict] | EmailAddressDict | list[str] | str
    bcc: list[EmailAddressDict] | EmailAddressDict | list[str] | str
    reply_to: EmailAddressDict | str
    content: list[ContentDict]
    text: str
    html: str
    headers: EmailHeaders
    attachments: list[AttachmentDict | Attachment]
    transactional: bool
    dkim_domain: str
    dkim_private_key: str
    dkim_selector: str
    envelope_from: EmailAddressDict
    campaign_id: str
    tracking_settings: TrackingSettingsDict
    unsubscribe_settings: UnsubscribeSettingsDict


class EmailAddress(BaseModel):
    """Email address used for senders and recipients."""

    model_config = ConfigDict(populate_by_name=True)

    email: str
    name: str | None = None

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        """Validate the basic shape of an email address."""
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            logger.error("Invalid email address shape email=%s", value)
            raise ValueError("email must contain a local part and domain")
        return value


class Content(BaseModel):
    """Email body content part."""

    type: Literal["text/plain", "text/html"] | str
    value: str
    template_type: Literal["mustache"] | None = None


class Attachment(BaseModel):
    """Email attachment encoded for the MailChannels API."""

    content: str
    filename: str
    type: str | None = None
    disposition: str | None = None
    content_id: str | None = None

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        *,
        filename: str,
        content_type: str | None = None,
        disposition: str = "attachment",
        content_id: str | None = None,
    ) -> Attachment:
        """Build an attachment from bytes."""
        logger.debug(
            "Encoding MailChannels attachment from bytes filename=%s",
            filename,
        )
        return cls(
            content=_base64_content(data),
            filename=filename,
            type=content_type or _guess_content_type(filename),
            disposition=disposition,
            content_id=content_id,
        )


class TrackingToggle(BaseModel):
    """Open or click tracking toggle for a MailChannels send."""

    enable: bool = False
    custom_domain_name: str | None = None


class TrackingSettings(BaseModel):
    """Open and click tracking settings for a MailChannels send."""

    open_tracking: TrackingToggle | None = None
    click_tracking: TrackingToggle | None = None


class UnsubscribeSettings(BaseModel):
    """Unsubscribe experience settings for a MailChannels send."""

    custom_domain_name: str | None = None


class Personalization(BaseModel):
    """Recipient-specific message customization."""

    model_config = ConfigDict(populate_by_name=True)

    to: list[EmailAddress] = Field(default_factory=list, min_length=1)
    cc: list[EmailAddress] | None = None
    bcc: list[EmailAddress] | None = None
    subject: str | None = None
    from_: EmailAddress | None = Field(
        default=None,        
        validation_alias=AliasChoices("from", "from_"),
        serialization_alias="from"
        )
    reply_to: EmailAddress | None = Field(default=None, alias="reply_to")
    envelope_from: EmailAddress | None = None
    headers: EmailHeaders | None = None
    substitutions: dict[str, str] | None = None
    dynamic_template_data: dict[str, Any] | None = None
    dkim_domain: str | None = None
    dkim_private_key: str | None = None
    dkim_selector: str | None = None

    @field_validator("headers")
    @classmethod
    def _validate_headers(cls, value: EmailHeaders | None) -> EmailHeaders | None:
        """Reject custom headers that are controlled by the API payload."""
        return _validate_custom_headers(value)


class EmailParams(BaseModel):
    """Validated MailChannels email send payload."""

    model_config = ConfigDict(populate_by_name=True)

    personalizations: list[Personalization] = Field(min_length=1)
    from_: EmailAddress = Field(
        validation_alias=AliasChoices("from", "from_"),
        serialization_alias="from"
        )
    subject: str = Field(min_length=1)
    content: list[Content] = Field(min_length=1)
    reply_to: EmailAddress | None = Field(default=None, alias="reply_to")
    envelope_from: EmailAddress | None = None
    headers: EmailHeaders | None = None
    attachments: list[Attachment] | None = None
    transactional: bool | None = None
    dkim_domain: str | None = None
    dkim_private_key: str | None = None
    dkim_selector: str | None = None
    campaign_id: str | None = None
    tracking_settings: TrackingSettings | None = None
    unsubscribe_settings: UnsubscribeSettings | None = None

    @field_validator("headers")
    @classmethod
    def _validate_headers(cls, value: EmailHeaders | None) -> EmailHeaders | None:
        """Reject custom headers that are controlled by the API payload."""
        return _validate_custom_headers(value)

    @field_validator("campaign_id")
    @classmethod
    def _validate_campaign_id(cls, value: str | None) -> str | None:
        """Enforce the campaign_id length and spacing rules."""
        if value is None:
            return None
        if " " in value:
            logger.error("MailChannels campaign_id contains spaces value=%r", value)
            raise ValueError("campaign_id must not contain spaces")
        if len(value.encode("utf-8")) > 48:
            logger.error("MailChannels campaign_id exceeds 48 UTF-8 bytes")
            raise ValueError("campaign_id must be at most 48 UTF-8 bytes")
        return value

    def to_payload(self) -> dict[str, Any]:
        """Convert this email model to a MailChannels API payload."""
        logger.debug("Serializing EmailParams subject=%s", self.subject)
        return self.model_dump(by_alias=True, exclude_none=True)


class SendResult(BaseModel):
    """Delivery handoff result for one send personalization."""

    model_config = ConfigDict(extra="allow")

    index: int
    message_id: str
    status: Literal["sent", "failed"]
    reason: str | None = None


class SendResponse(BaseModel):
    """Response returned by the MailChannels `/send` endpoint."""

    model_config = ConfigDict(extra="allow")

    request_id: str | None = None
    results: list[SendResult] | None = None
    data: list[str] | None = None

    @field_validator("results")
    @classmethod
    def _validate_send_results(
        cls,
        value: list[SendResult] | None,
    ) -> list[SendResult] | None:
        """Require normal send responses to include at least one result."""
        if value is not None and len(value) == 0:
            logger.error("MailChannels send response included no results")
            raise ValueError("send results must not be empty")
        return value

    @field_validator("data")
    @classmethod
    def _validate_dry_run_data(cls, value: list[str] | None) -> list[str] | None:
        """Require dry-run send responses to include rendered message data."""
        if value is not None and len(value) == 0:
            logger.error("MailChannels dry-run response included no rendered data")
            raise ValueError("dry-run data must not be empty")
        return value

    @field_validator("request_id")
    @classmethod
    def _validate_send_shape(cls, value: str | None) -> str | None:
        """Keep request IDs non-empty when the API returns them."""
        if value == "":
            logger.error("MailChannels send response included an empty request_id")
            raise ValueError("request_id must not be empty")
        return value

    @model_validator(mode="after")
    def _validate_response_variant(self) -> SendResponse:
        """Validate that `/send` returned either send results or dry-run data."""
        has_send_results = self.request_id is not None and self.results is not None
        has_dry_run_data = self.data is not None
        if not has_send_results and not has_dry_run_data:
            logger.error("MailChannels send response missing results or dry-run data")
            raise ValueError("send response must include request_id/results or data")
        return self


class QueuedSendResponse(BaseModel):
    """Response returned when MailChannels queues an email for async processing."""

    model_config = ConfigDict(extra="allow")

    request_id: str
    queued_at: datetime


def _base64_content(data: bytes) -> str:
    """Return Base64-encoded attachment content."""
    return base64.b64encode(data).decode("ascii")


def _guess_content_type(filename: str) -> str:
    """Infer a MIME type for an attachment filename."""
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


def _validate_custom_headers(value: EmailHeaders | None) -> EmailHeaders | None:
    """Validate that custom header names do not duplicate structured fields."""
    if value is None:
        return None
    reserved = sorted(
        header for header in value if header.lower() in RESERVED_EMAIL_HEADERS
    )
    if reserved:
        logger.error("Reserved email headers are not allowed headers=%s", reserved)
        raise ValueError(
            "custom headers cannot include reserved message headers: "
            + ", ".join(reserved)
        )
    return value
