"""HTTP response helpers for the MailChannels SDK."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .exceptions import (
    ApiError,
    AuthenticationError,
    BadGatewayError,
    ConflictError,
    ForbiddenError,
    InvalidRequestError,
    NotFoundError,
    PayloadTooLargeError,
    RateLimitError,
    ResponseValidationError,
    ServerError,
)

# Status-code-specific subclasses. Adding a new exception means dropping
# the class onto this list — _STATUS_DISPATCH derives its mapping from
# each class's `status_code` ClassVar. Order is informational; the dict
# resolves uniquely on status_code.
_API_ERROR_CLASSES: tuple[type[ApiError], ...] = (
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    PayloadTooLargeError,
    RateLimitError,
    BadGatewayError,
)

_STATUS_DISPATCH: dict[int, type[ApiError]] = {
    cls.default_status_code: cls
    for cls in _API_ERROR_CLASSES
    if cls.default_status_code is not None
}

logger = logging.getLogger(__name__)
ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


@dataclass(frozen=True)
class SDKResponse:
    """Normalized HTTP response returned by SDK transports."""

    status_code: int
    data: Any
    text: str
    headers: dict[str, str] | None = None


class MailChannelsResponse(dict[str, Any]):
    """Dict response that also supports attribute-style access."""

    def __getattr__(self, name: str) -> Any:
        """Return a response value as an attribute."""
        try:
            return self[name]
        except KeyError as error:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            ) from error


class EmptyResponse(BaseModel):
    """Response model for endpoints that intentionally return no body.

    The MailChannels API returns 201/204 with no payload for several mutations
    (delete, suspend, activate, status updates). This model preserves the
    response headers for diagnostics — request IDs, rate-limit hints — without
    inventing fake content.
    """

    model_config = ConfigDict(extra="allow")

    http_headers: dict[str, str] = Field(default_factory=dict)


def response_data(response: SDKResponse) -> MailChannelsResponse:
    """Convert an SDK response into the public response object."""
    headers = dict(response.headers or {})
    if isinstance(response.data, dict):
        data = MailChannelsResponse(response.data)
        data["http_headers"] = headers
        return data
    if isinstance(response.data, list):
        return MailChannelsResponse({"data": response.data, "http_headers": headers})
    return MailChannelsResponse({"http_headers": headers})


def response_model_data(
    response: SDKResponse,
    response_model: type[ResponseModel],
) -> ResponseModel:
    """Convert an SDK response into a typed Pydantic response model."""
    data = response_data(response)
    try:
        parsed = response_model.model_validate(data)
    except ValidationError as error:
        logger.error(
            "MailChannels response validation failed model=%s error=%s",
            response_model.__name__,
            error,
        )
        raise ResponseValidationError(
            "MailChannels API response did not match the expected model.",
            code="ResponseValidationError",
            response=data,
            headers=dict(response.headers or {}),
        ) from error
    logger.debug("Validated MailChannels response model=%s", response_model.__name__)
    return parsed


def raise_for_status(response: SDKResponse) -> None:
    """Raise a typed SDK exception for non-success API responses."""
    if 200 <= response.status_code < 300:
        logger.debug(
            "MailChannels API response accepted status=%s",
            response.status_code,
        )
        return

    message = _error_message(response)
    logger.error(
        "MailChannels API request failed status=%s message=%s",
        response.status_code,
        message,
    )

    error_class = _STATUS_DISPATCH.get(response.status_code)
    if error_class is None:
        if 500 <= response.status_code:
            error_class = ServerError
        elif 400 <= response.status_code:
            error_class = InvalidRequestError
        else:
            error_class = ApiError

    raise error_class(
        message,
        status_code=response.status_code,
        response=response.data,
        headers=response.headers,
    )


def _error_message(response: SDKResponse) -> str:
    """Extract a useful message from a MailChannels response."""
    if isinstance(response.data, dict):
        for key in ("message", "error", "detail", "title"):
            value = response.data.get(key)
            if isinstance(value, str) and value:
                return value
    text = response.text.strip()
    if text and text.lower() != "null":
        return text
    return f"MailChannels API request failed with status {response.status_code}."
