"""Email resource implementation."""

from __future__ import annotations

import logging
from typing import Any, Generic, Literal, TypeVar, overload

from pydantic import ValidationError

from ..exceptions import MailChannelsError
from ..response import MailChannelsResponse
from .types import EmailAddress, EmailParams, QueuedSendResponse, SendResponse
from .types import SendParams as SendParamsType

logger = logging.getLogger(__name__)
StrictResponses = TypeVar("StrictResponses", bound=bool)


class EmailsResource(Generic[StrictResponses]):
    """Client-bound email operations."""

    def __init__(self, client: Any) -> None:
        """Create an email resource bound to a client."""
        self._client = client

    @overload
    def send(
        self: EmailsResource[Literal[True]],
        params: SendParamsType | EmailParams,
        *,
        dry_run: bool = False,
    ) -> SendResponse: ...

    @overload
    def send(
        self: EmailsResource[Literal[False]],
        params: SendParamsType | EmailParams,
        *,
        dry_run: bool = False,
    ) -> MailChannelsResponse: ...

    @overload
    def send(
        self,
        params: SendParamsType | EmailParams,
        *,
        dry_run: bool = False,
    ) -> SendResponse | MailChannelsResponse: ...

    def send(
        self,
        params: SendParamsType | EmailParams,
        *,
        dry_run: bool = False,
    ) -> SendResponse | MailChannelsResponse:
        """Send an email through the synchronous `/send` endpoint.

        This is the documented `/send` endpoint and accepts/rejects the
        payload synchronously: validation errors come back in the response.
        For higher throughput where you want MailChannels to accept the
        message and process it in the background, use `queue()` instead.

        The trailing `_async` on `send_async()` refers to **Python asyncio**,
        not to the MailChannels server-side queue. `send_async()` is the
        asyncio version of this same `/send` call.
        """
        payload = normalize_email_params(params)
        query = {"dry-run": "true"} if dry_run else None
        logger.info("Sending email through MailChannels dry_run=%s", dry_run)
        return self._client.request(
            "POST",
            "/send",
            json=payload,
            params=query,
            response_model=SendResponse,
        )

    @overload
    async def send_async(
        self: EmailsResource[Literal[True]],
        params: SendParamsType | EmailParams,
        *,
        dry_run: bool = False,
    ) -> SendResponse: ...

    @overload
    async def send_async(
        self: EmailsResource[Literal[False]],
        params: SendParamsType | EmailParams,
        *,
        dry_run: bool = False,
    ) -> MailChannelsResponse: ...

    @overload
    async def send_async(
        self,
        params: SendParamsType | EmailParams,
        *,
        dry_run: bool = False,
    ) -> SendResponse | MailChannelsResponse: ...

    async def send_async(
        self,
        params: SendParamsType | EmailParams,
        *,
        dry_run: bool = False,
    ) -> SendResponse | MailChannelsResponse:
        """Send an email through `/send` using Python asyncio (httpx).

        This is the asyncio version of `send()`. It hits the same `/send`
        endpoint synchronously on the server side. To hand the message to
        MailChannels' server-side queue, use `queue_async()`.
        """
        payload = normalize_email_params(params)
        query = {"dry-run": "true"} if dry_run else None
        logger.info("Sending email through MailChannels async HTTP dry_run=%s", dry_run)
        return await self._client.request_async(
            "POST",
            "/send",
            json=payload,
            params=query,
            response_model=SendResponse,
        )

    @overload
    def queue(
        self: EmailsResource[Literal[True]],
        params: SendParamsType | EmailParams,
    ) -> QueuedSendResponse: ...

    @overload
    def queue(
        self: EmailsResource[Literal[False]],
        params: SendParamsType | EmailParams,
    ) -> MailChannelsResponse: ...

    @overload
    def queue(
        self,
        params: SendParamsType | EmailParams,
    ) -> QueuedSendResponse | MailChannelsResponse: ...

    def queue(
        self,
        params: SendParamsType | EmailParams,
    ) -> QueuedSendResponse | MailChannelsResponse:
        """Queue an email through MailChannels' `/send-async` endpoint.

        `queue()` performs the same request validation as `send()`
        (sender/recipient addresses, content, template syntax, attachments,
        headers, payload size) and returns 4xx for a malformed request. The
        difference is latency: `/send-async` defers some per-recipient
        processing into the background so the request returns faster.
        Delivery semantics are otherwise the same as `send()`, including how
        bounces and other delivery events are reported via webhooks.

        Despite the name overlap, this is **not** the same as `send_async()`:
        the `_async` suffix elsewhere refers to Python asyncio. To call
        `/send-async` from asyncio code, use `queue_async()`.
        """
        payload = normalize_email_params(params)
        logger.info("Queueing email through MailChannels /send-async")
        return self._client.request(
            "POST",
            "/send-async",
            json=payload,
            response_model=QueuedSendResponse,
        )

    @overload
    async def queue_async(
        self: EmailsResource[Literal[True]],
        params: SendParamsType | EmailParams,
    ) -> QueuedSendResponse: ...

    @overload
    async def queue_async(
        self: EmailsResource[Literal[False]],
        params: SendParamsType | EmailParams,
    ) -> MailChannelsResponse: ...

    @overload
    async def queue_async(
        self,
        params: SendParamsType | EmailParams,
    ) -> QueuedSendResponse | MailChannelsResponse: ...

    async def queue_async(
        self,
        params: SendParamsType | EmailParams,
    ) -> QueuedSendResponse | MailChannelsResponse:
        """Queue an email through `/send-async` using Python asyncio (httpx).

        This is the asyncio version of `queue()`. It uses the same MailChannels
        server-side queue; the `_async` suffix refers to Python asyncio.
        """
        payload = normalize_email_params(params)
        logger.info("Queueing email through MailChannels /send-async using async HTTP")
        return await self._client.request_async(
            "POST",
            "/send-async",
            json=payload,
            response_model=QueuedSendResponse,
        )


class Emails:
    """Module-level email operations using global SDK configuration."""

    SendParams = SendParamsType

    @classmethod
    def send(
        cls,
        params: SendParamsType | EmailParams,
        *,
        dry_run: bool = False,
    ) -> SendResponse | MailChannelsResponse:
        """Send an email through the globally configured client."""
        from ..client import get_default_client

        return get_default_client().emails.send(params, dry_run=dry_run)

    @classmethod
    async def send_async(
        cls,
        params: SendParamsType | EmailParams,
        *,
        dry_run: bool = False,
    ) -> SendResponse | MailChannelsResponse:
        """Send an email through the globally configured async client."""
        from ..client import get_default_client

        return await get_default_client().emails.send_async(params, dry_run=dry_run)

    @classmethod
    def queue(
        cls,
        params: SendParamsType | EmailParams,
    ) -> QueuedSendResponse | MailChannelsResponse:
        """Queue an email through the globally configured client."""
        from ..client import get_default_client

        return get_default_client().emails.queue(params)

    @classmethod
    async def queue_async(
        cls,
        params: SendParamsType | EmailParams,
    ) -> QueuedSendResponse | MailChannelsResponse:
        """Queue an email through the globally configured async client."""
        from ..client import get_default_client

        return await get_default_client().emails.queue_async(params)


def normalize_email_params(params: SendParamsType | EmailParams) -> dict[str, Any]:
    """Normalize SDK email parameters into MailChannels API JSON."""
    if isinstance(params, EmailParams):
        return params.to_payload()
    try:
        payload = _normalize_mapping(params)
        email_params = EmailParams.model_validate(payload)
        return email_params.to_payload()
    except ValidationError as error:
        logger.error("Invalid MailChannels email parameters: %s", error)
        raise MailChannelsError(
            "Invalid email parameters.",
            code="ValidationError",
        ) from error


def _normalize_mapping(params: SendParamsType) -> dict[str, Any]:
    """Normalize dictionary email parameters into MailChannels structure."""
    payload: dict[str, Any] = dict(params)
    from_value = _extract_from(payload)
    content = payload.get("content") or _content_from_shortcuts(payload)
    personalizations = payload.get("personalizations") or [
        _personalization_from_shortcuts(payload)
    ]
    normalized = {
        "from": from_value,
        "subject": payload.get("subject"),
        "content": content,
        "personalizations": personalizations,
    }
    _copy_optional(payload, normalized, "reply_to")
    _copy_optional(payload, normalized, "envelope_from")
    _copy_optional(payload, normalized, "headers")
    _copy_optional(payload, normalized, "attachments")
    _copy_optional(payload, normalized, "transactional")
    _copy_optional(payload, normalized, "dkim_domain")
    _copy_optional(payload, normalized, "dkim_private_key")
    _copy_optional(payload, normalized, "dkim_selector")
    _copy_optional(payload, normalized, "campaign_id")
    _copy_optional(payload, normalized, "tracking_settings")
    return normalized


def _extract_from(payload: dict[str, Any]) -> Any:
    """Extract a sender field from supported aliases."""
    for key in ("from", "from_", "from_email", "from_address", "from_field"):
        if key in payload:
            return _address(payload[key])
    logger.error("Email payload is missing sender")
    raise MailChannelsError(
        "Email parameters must include `from`.",
        code="ValidationError",
    )


def _content_from_shortcuts(payload: dict[str, Any]) -> list[dict[str, str]]:
    """Build MailChannels content parts from `text` and `html` shortcuts."""
    content: list[dict[str, str]] = []
    if payload.get("text"):
        content.append({"type": "text/plain", "value": str(payload["text"])})
    if payload.get("html"):
        content.append({"type": "text/html", "value": str(payload["html"])})
    if not content:
        logger.error("Email payload is missing content")
        raise MailChannelsError(
            "Email parameters must include `content`, `text`, or `html`.",
            code="ValidationError",
        )
    return content


def _personalization_from_shortcuts(payload: dict[str, Any]) -> dict[str, Any]:
    """Build a MailChannels personalization from recipient shortcuts."""
    if "to" not in payload:
        logger.error("Email payload is missing recipients")
        raise MailChannelsError(
            "Email parameters must include `to`.",
            code="ValidationError",
        )
    personalization: dict[str, Any] = {"to": _addresses(payload["to"])}
    if payload.get("cc"):
        personalization["cc"] = _addresses(payload["cc"])
    if payload.get("bcc"):
        personalization["bcc"] = _addresses(payload["bcc"])
    return personalization


def _addresses(value: Any) -> list[dict[str, Any]]:
    """Normalize one or many email addresses."""
    if isinstance(value, list):
        return [_address(item) for item in value]
    return [_address(value)]


def _address(value: Any) -> dict[str, Any]:
    """Normalize one email address."""
    if isinstance(value, EmailAddress):
        return value.model_dump(exclude_none=True)
    if isinstance(value, str):
        return {"email": value}
    if isinstance(value, dict):
        return value
    logger.error("Unsupported email address value type=%s", type(value).__name__)
    raise MailChannelsError(
        "Email address must be a string or mapping.",
        code="ValidationError",
    )


def _copy_optional(source: dict[str, Any], target: dict[str, Any], key: str) -> None:
    """Copy an optional key when it has a non-empty value."""
    if source.get(key) is not None:
        target[key] = source[key]
