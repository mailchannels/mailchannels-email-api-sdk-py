"""Exceptions raised by the MailChannels SDK."""

from __future__ import annotations

import logging
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class MailChannelsError(Exception):
    """Base class for MailChannels SDK errors."""

    # Subclasses set these to co-locate diagnostic metadata with the class
    # they describe. Leave as None to fall through to code-based or
    # status-code-range defaults.
    default_status_code: ClassVar[int | None] = None
    default_error_type: ClassVar[str | None] = None
    default_suggested_action: ClassVar[str | None] = None

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        response: Any | None = None,
        headers: dict[str, str] | None = None,
        error_type: str | None = None,
        request_id: str | None = None,
        suggested_action: str | None = None,
    ) -> None:
        """Initialize a MailChannels error."""
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.response = response
        self.headers = dict(headers or {})
        self.error_type = error_type or _resolve_error_type(self, code, status_code)
        self.request_id = request_id or _request_id(self.headers)
        self.retry_after = self.headers.get("Retry-After")
        self.suggested_action = suggested_action or _resolve_suggested_action(
            self,
            code,
        )
        logger.debug(
            "Initialized MailChannelsError code=%s status=%s request_id=%s",
            code,
            status_code,
            self.request_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return structured metadata for logging or diagnostics."""
        return {
            "message": self.message,
            "status_code": self.status_code,
            "code": self.code,
            "error_type": self.error_type,
            "request_id": self.request_id,
            "retry_after": self.retry_after,
            "suggested_action": self.suggested_action,
            "headers": self.headers,
            "response": self.response,
        }


class ConfigurationError(MailChannelsError):
    """Raised when SDK configuration is missing or invalid."""


class ApiError(MailChannelsError):
    """Raised for MailChannels API failures."""


class AuthenticationError(ApiError):
    """Raised when MailChannels rejects authentication."""

    default_status_code = 401
    default_error_type = "authentication_error"
    default_suggested_action = "Check that the MailChannels API key is valid."


class ForbiddenError(ApiError):
    """Raised when an account cannot access a requested feature."""

    default_status_code = 403
    default_error_type = "permission_error"
    default_suggested_action = (
        "Confirm the API key has access to this MailChannels resource."
    )


class ConflictError(ApiError):
    """Raised when MailChannels reports a resource conflict."""

    default_status_code = 409
    default_error_type = "conflict_error"
    default_suggested_action = (
        "Use the existing resource or retry with a unique identifier."
    )


class NotFoundError(ApiError):
    """Raised when MailChannels reports the requested resource does not exist."""

    default_status_code = 404
    default_error_type = "not_found"
    default_suggested_action = (
        "Confirm the resource identifier exists for this account."
    )


class PayloadTooLargeError(ApiError):
    """Raised when a request payload exceeds MailChannels limits."""

    default_status_code = 413
    default_error_type = "payload_too_large"
    default_suggested_action = (
        "Reduce message size or attachment payload before retrying."
    )


class RateLimitError(ApiError):
    """Raised when MailChannels asks the caller to slow down."""

    default_status_code = 429
    default_error_type = "rate_limit_error"
    default_suggested_action = (
        "Back off before retrying; inspect Retry-After if present."
    )


class InvalidRequestError(ApiError):
    """Raised when MailChannels rejects request parameters or payload shape."""

    default_error_type = "invalid_request_error"


class ServerError(ApiError):
    """Raised when MailChannels returns a server-side failure."""

    default_error_type = "server_error"
    default_suggested_action = (
        "Retry later or contact MailChannels support with the request ID."
    )


class BadGatewayError(ServerError):
    """Raised when MailChannels returns a bad gateway response."""

    default_status_code = 502


class ResponseValidationError(MailChannelsError):
    """Raised when strict response validation fails."""

    default_error_type = "response_validation_error"
    default_suggested_action = (
        "Inspect the API response shape and SDK response model."
    )


class AsyncClientNotConfigured(ConfigurationError):
    """Raised when async support is requested without an async HTTP client."""


def _request_id(headers: dict[str, str]) -> str | None:
    """Extract a request identifier from response headers."""
    request_id_headers = (
        "X-Request-ID",
        "X-Request-Id",
        "Request-ID",
        "X-Correlation-ID",
        "X-Amzn-Trace-Id",
    )
    lowered = {key.lower(): value for key, value in headers.items()}
    for header in request_id_headers:
        value = lowered.get(header.lower())
        if value:
            return value
    return None


def _resolve_error_type(
    error: MailChannelsError,
    code: str | None,
    status_code: int | None,
) -> str | None:
    """Return a stable error type, preferring class metadata over raw code."""
    cls_default = type(error).default_error_type
    if cls_default is not None:
        return cls_default
    if code:
        return code
    if status_code is None:
        return None
    if 500 <= status_code:
        return "server_error"
    if 400 <= status_code:
        return "invalid_request_error"
    return "api_error"


def _resolve_suggested_action(
    error: MailChannelsError,
    code: str | None,
) -> str | None:
    """Return a concise remediation hint, preferring class metadata."""
    if code == "MissingApiKey":
        return "Configure MAILCHANNELS_API_KEY or pass api_key to Client."
    return type(error).default_suggested_action
