"""Python SDK for the MailChannels Email API."""

from __future__ import annotations

import os

from .check_domain import (
    CheckDomain,
    CheckDomainParams,
    CheckDomainResource,
    CheckDomainResult,
    CheckResults,
    DkimResult,
    DkimSetting,
    DomainCheckVerdict,
    LockdownResult,
    SenderDomainResult,
    SpfResult,
)
from .client import DEFAULT_BASE_URL, Client
from .compatibility import API_SPEC_COMPATIBILITY, ApiSpecCompatibility
from .dkim import Dkim
from .emails import (
    UNSUBSCRIBE_URL_PLACEHOLDER,
    Attachment,
    Content,
    EmailAddress,
    EmailHeaders,
    EmailParams,
    Emails,
    Personalization,
    QueuedSendResponse,
    SendParams,
    SendResponse,
    SendResult,
    TrackingSettings,
    TrackingToggle,
)
from .exceptions import (
    ApiError,
    AsyncClientNotConfigured,
    AuthenticationError,
    BadGatewayError,
    ConfigurationError,
    ConflictError,
    ForbiddenError,
    InvalidRequestError,
    MailChannelsError,
    NotFoundError,
    PayloadTooLargeError,
    RateLimitError,
    ResponseValidationError,
    ServerError,
)
from .http_client import RequestsClient
from .http_client_async import HTTPXClient
from .http_protocols import AsyncHTTPClient, SyncHTTPClient
from .metrics import Metrics
from .response import EmptyResponse, SDKResponse
from .sub_accounts import SubAccounts
from .suppressions import Suppressions
from .usage import Usage, UsageStats
from .version import __version__, get_version
from .webhooks import (
    SignatureParameters,
    WebhookEventPayload,
    Webhooks,
    parse_signature_input,
    signature_is_fresh,
    signature_key_id,
    verify_content_digest,
    verify_webhook_signature,
)

api_key: str | None = os.environ.get("MAILCHANNELS_API_KEY")
base_url: str = os.environ.get("MAILCHANNELS_API_URL", DEFAULT_BASE_URL)
default_http_client: RequestsClient | None = None
default_async_http_client: HTTPXClient | None = None
strict_responses: bool = False

__all__ = [
    "ApiError",
    "ApiSpecCompatibility",
    "AsyncHTTPClient",
    "AsyncClientNotConfigured",
    "Attachment",
    "AuthenticationError",
    "BadGatewayError",
    "Client",
    "ConfigurationError",
    "ConflictError",
    "Content",
    "CheckDomainParams",
    "CheckDomain",
    "CheckDomainResult",
    "CheckDomainResource",
    "CheckResults",
    "Dkim",
    "DkimResult",
    "DkimSetting",
    "DomainCheckVerdict",
    "EmailAddress",
    "EmptyResponse",
    "EmailHeaders",
    "EmailParams",
    "Emails",
    "ForbiddenError",
    "HTTPXClient",
    "InvalidRequestError",
    "LockdownResult",
    "MailChannelsError",
    "Metrics",
    "NotFoundError",
    "PayloadTooLargeError",
    "Personalization",
    "QueuedSendResponse",
    "RateLimitError",
    "ResponseValidationError",
    "RequestsClient",
    "SendParams",
    "SendResponse",
    "SendResult",
    "SenderDomainResult",
    "ServerError",
    "SDKResponse",
    "SignatureParameters",
    "SpfResult",
    "SubAccounts",
    "Suppressions",
    "SyncHTTPClient",
    "TrackingSettings",
    "TrackingToggle",
    "UNSUBSCRIBE_URL_PLACEHOLDER",
    "Usage",
    "UsageStats",
    "WebhookEventPayload",
    "Webhooks",
    "API_SPEC_COMPATIBILITY",
    "__version__",
    "api_key",
    "base_url",
    "default_async_http_client",
    "default_http_client",
    "get_version",
    "strict_responses",
    "parse_signature_input",
    "signature_is_fresh",
    "signature_key_id",
    "verify_content_digest",
    "verify_webhook_signature",
]
