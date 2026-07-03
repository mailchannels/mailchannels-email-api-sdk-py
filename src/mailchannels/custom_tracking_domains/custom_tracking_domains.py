"""Custom tracking domain resource implementation."""

from __future__ import annotations

import logging
from typing import Any, Generic, Literal, TypeVar, overload

from ..paths import encode_path_segments
from ..query import pagination_query
from ..response import EmptyResponse, MailChannelsResponse
from .types import (
    CustomTrackingDomainListResponse,
    CustomTrackingDomainResult,
    CustomTrackingScope,
    CustomTrackingStatus,
)

logger = logging.getLogger(__name__)
StrictResponses = TypeVar("StrictResponses", bound=bool)


class CustomTrackingDomainsResource(Generic[StrictResponses]):
    """Client-bound custom tracking domain operations."""

    def __init__(self, client: Any) -> None:
        """Create a custom tracking domains resource bound to a client."""
        self._client = client

    @overload
    def list(
        self: CustomTrackingDomainsResource[Literal[True]],
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
        scope: CustomTrackingScope | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> CustomTrackingDomainListResponse: ...

    @overload
    def list(
        self: CustomTrackingDomainsResource[Literal[False]],
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
        scope: CustomTrackingScope | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> MailChannelsResponse: ...

    @overload
    def list(
        self,
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
        scope: CustomTrackingScope | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> CustomTrackingDomainListResponse | MailChannelsResponse: ...

    def list(
        self,
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
        scope: CustomTrackingScope | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> CustomTrackingDomainListResponse | MailChannelsResponse:
        """Retrieve custom tracking domains registered under this account."""
        logger.info(
            "Listing MailChannels custom tracking domains name=%s status=%s scope=%s",
            name,
            status,
            scope,
        )
        params = pagination_query(
            limit=limit,
            offset=offset,
            name=name,
            status=status,
            scope=scope,
        )
        return self._client.request(
            "GET",
            "/custom-tracking-domains",
            params=params or None,
            response_model=CustomTrackingDomainListResponse,
        )

    @overload
    async def list_async(
        self: CustomTrackingDomainsResource[Literal[True]],
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
        scope: CustomTrackingScope | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> CustomTrackingDomainListResponse: ...

    @overload
    async def list_async(
        self: CustomTrackingDomainsResource[Literal[False]],
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
        scope: CustomTrackingScope | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> MailChannelsResponse: ...

    @overload
    async def list_async(
        self,
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
        scope: CustomTrackingScope | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> CustomTrackingDomainListResponse | MailChannelsResponse: ...

    async def list_async(
        self,
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
        scope: CustomTrackingScope | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> CustomTrackingDomainListResponse | MailChannelsResponse:
        """Retrieve custom tracking domains using async HTTP."""
        logger.info(
            "Listing MailChannels custom tracking domains using async HTTP "
            "name=%s status=%s scope=%s",
            name,
            status,
            scope,
        )
        params = pagination_query(
            limit=limit,
            offset=offset,
            name=name,
            status=status,
            scope=scope,
        )
        return await self._client.request_async(
            "GET",
            "/custom-tracking-domains",
            params=params or None,
            response_model=CustomTrackingDomainListResponse,
        )

    @overload
    def create(
        self: CustomTrackingDomainsResource[Literal[True]],
        *,
        name: str,
        hostname: str,
        scope: CustomTrackingScope,
    ) -> CustomTrackingDomainResult: ...

    @overload
    def create(
        self: CustomTrackingDomainsResource[Literal[False]],
        *,
        name: str,
        hostname: str,
        scope: CustomTrackingScope,
    ) -> MailChannelsResponse: ...

    @overload
    def create(
        self,
        *,
        name: str,
        hostname: str,
        scope: CustomTrackingScope,
    ) -> CustomTrackingDomainResult | MailChannelsResponse: ...

    def create(
        self,
        *,
        name: str,
        hostname: str,
        scope: CustomTrackingScope,
    ) -> CustomTrackingDomainResult | MailChannelsResponse:
        """Register a custom tracking domain for click, open, or unsubscribe links."""
        logger.info(
            "Registering MailChannels custom tracking domain name=%s hostname=%s "
            "scope=%s",
            name,
            hostname,
            scope,
        )
        return self._client.request(
            "POST",
            "/custom-tracking-domains",
            json={"name": name, "hostname": hostname, "scope": scope},
            response_model=CustomTrackingDomainResult,
        )

    @overload
    async def create_async(
        self: CustomTrackingDomainsResource[Literal[True]],
        *,
        name: str,
        hostname: str,
        scope: CustomTrackingScope,
    ) -> CustomTrackingDomainResult: ...

    @overload
    async def create_async(
        self: CustomTrackingDomainsResource[Literal[False]],
        *,
        name: str,
        hostname: str,
        scope: CustomTrackingScope,
    ) -> MailChannelsResponse: ...

    @overload
    async def create_async(
        self,
        *,
        name: str,
        hostname: str,
        scope: CustomTrackingScope,
    ) -> CustomTrackingDomainResult | MailChannelsResponse: ...

    async def create_async(
        self,
        *,
        name: str,
        hostname: str,
        scope: CustomTrackingScope,
    ) -> CustomTrackingDomainResult | MailChannelsResponse:
        """Register a custom tracking domain using async HTTP."""
        logger.info(
            "Registering MailChannels custom tracking domain using async HTTP "
            "name=%s hostname=%s scope=%s",
            name,
            hostname,
            scope,
        )
        return await self._client.request_async(
            "POST",
            "/custom-tracking-domains",
            json={"name": name, "hostname": hostname, "scope": scope},
            response_model=CustomTrackingDomainResult,
        )

    @overload
    def update(
        self: CustomTrackingDomainsResource[Literal[True]],
        hostname: str,
        scope: CustomTrackingScope,
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
    ) -> CustomTrackingDomainResult: ...

    @overload
    def update(
        self: CustomTrackingDomainsResource[Literal[False]],
        hostname: str,
        scope: CustomTrackingScope,
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
    ) -> MailChannelsResponse: ...

    @overload
    def update(
        self,
        hostname: str,
        scope: CustomTrackingScope,
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
    ) -> CustomTrackingDomainResult | MailChannelsResponse: ...

    def update(
        self,
        hostname: str,
        scope: CustomTrackingScope,
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
    ) -> CustomTrackingDomainResult | MailChannelsResponse:
        """Update a custom tracking domain's label or active status."""
        logger.info(
            "Updating MailChannels custom tracking domain hostname=%s scope=%s "
            "name=%s status=%s",
            hostname,
            scope,
            name,
            status,
        )
        payload = _compact({"name": name, "status": status})
        return self._client.request(
            "PATCH",
            encode_path_segments("custom-tracking-domains", hostname, scope),
            json=payload,
            response_model=CustomTrackingDomainResult,
        )

    @overload
    async def update_async(
        self: CustomTrackingDomainsResource[Literal[True]],
        hostname: str,
        scope: CustomTrackingScope,
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
    ) -> CustomTrackingDomainResult: ...

    @overload
    async def update_async(
        self: CustomTrackingDomainsResource[Literal[False]],
        hostname: str,
        scope: CustomTrackingScope,
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
    ) -> MailChannelsResponse: ...

    @overload
    async def update_async(
        self,
        hostname: str,
        scope: CustomTrackingScope,
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
    ) -> CustomTrackingDomainResult | MailChannelsResponse: ...

    async def update_async(
        self,
        hostname: str,
        scope: CustomTrackingScope,
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
    ) -> CustomTrackingDomainResult | MailChannelsResponse:
        """Update a custom tracking domain using async HTTP."""
        logger.info(
            "Updating MailChannels custom tracking domain using async HTTP "
            "hostname=%s scope=%s name=%s status=%s",
            hostname,
            scope,
            name,
            status,
        )
        payload = _compact({"name": name, "status": status})
        return await self._client.request_async(
            "PATCH",
            encode_path_segments("custom-tracking-domains", hostname, scope),
            json=payload,
            response_model=CustomTrackingDomainResult,
        )

    def delete(
        self,
        hostname: str,
        scope: CustomTrackingScope,
    ) -> EmptyResponse | MailChannelsResponse:
        """Permanently delete a custom tracking domain."""
        logger.info(
            "Deleting MailChannels custom tracking domain hostname=%s scope=%s",
            hostname,
            scope,
        )
        return self._client.request(
            "DELETE",
            encode_path_segments("custom-tracking-domains", hostname, scope),
            response_model=EmptyResponse,
        )

    async def delete_async(
        self,
        hostname: str,
        scope: CustomTrackingScope,
    ) -> EmptyResponse | MailChannelsResponse:
        """Permanently delete a custom tracking domain using async HTTP."""
        logger.info(
            "Deleting MailChannels custom tracking domain using async HTTP "
            "hostname=%s scope=%s",
            hostname,
            scope,
        )
        return await self._client.request_async(
            "DELETE",
            encode_path_segments("custom-tracking-domains", hostname, scope),
            response_model=EmptyResponse,
        )


class CustomTrackingDomains:
    """Module-level custom tracking domain operations using global SDK configuration."""

    @classmethod
    def list(
        cls,
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
        scope: CustomTrackingScope | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> CustomTrackingDomainListResponse | MailChannelsResponse:
        """Retrieve custom tracking domains registered under this account."""
        from ..client import get_default_client

        return get_default_client().custom_tracking_domains.list(
            name=name,
            status=status,
            scope=scope,
            limit=limit,
            offset=offset,
        )

    @classmethod
    async def list_async(
        cls,
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
        scope: CustomTrackingScope | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> CustomTrackingDomainListResponse | MailChannelsResponse:
        """Retrieve custom tracking domains using async HTTP."""
        from ..client import get_default_client

        return await get_default_client().custom_tracking_domains.list_async(
            name=name,
            status=status,
            scope=scope,
            limit=limit,
            offset=offset,
        )

    @classmethod
    def create(
        cls,
        *,
        name: str,
        hostname: str,
        scope: CustomTrackingScope,
    ) -> CustomTrackingDomainResult | MailChannelsResponse:
        """Register a custom tracking domain for click, open, or unsubscribe links."""
        from ..client import get_default_client

        return get_default_client().custom_tracking_domains.create(
            name=name,
            hostname=hostname,
            scope=scope,
        )

    @classmethod
    async def create_async(
        cls,
        *,
        name: str,
        hostname: str,
        scope: CustomTrackingScope,
    ) -> CustomTrackingDomainResult | MailChannelsResponse:
        """Register a custom tracking domain using async HTTP."""
        from ..client import get_default_client

        return await get_default_client().custom_tracking_domains.create_async(
            name=name,
            hostname=hostname,
            scope=scope,
        )

    @classmethod
    def update(
        cls,
        hostname: str,
        scope: CustomTrackingScope,
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
    ) -> CustomTrackingDomainResult | MailChannelsResponse:
        """Update a custom tracking domain's label or active status."""
        from ..client import get_default_client

        return get_default_client().custom_tracking_domains.update(
            hostname,
            scope,
            name=name,
            status=status,
        )

    @classmethod
    async def update_async(
        cls,
        hostname: str,
        scope: CustomTrackingScope,
        *,
        name: str | None = None,
        status: CustomTrackingStatus | None = None,
    ) -> CustomTrackingDomainResult | MailChannelsResponse:
        """Update a custom tracking domain using async HTTP."""
        from ..client import get_default_client

        return await get_default_client().custom_tracking_domains.update_async(
            hostname,
            scope,
            name=name,
            status=status,
        )

    @classmethod
    def delete(
        cls,
        hostname: str,
        scope: CustomTrackingScope,
    ) -> EmptyResponse | MailChannelsResponse:
        """Permanently delete a custom tracking domain."""
        from ..client import get_default_client

        return get_default_client().custom_tracking_domains.delete(hostname, scope)

    @classmethod
    async def delete_async(
        cls,
        hostname: str,
        scope: CustomTrackingScope,
    ) -> EmptyResponse | MailChannelsResponse:
        """Permanently delete a custom tracking domain using async HTTP."""
        from ..client import get_default_client

        return await get_default_client().custom_tracking_domains.delete_async(
            hostname,
            scope,
        )


def _compact(values: dict[str, Any]) -> dict[str, Any]:
    """Remove unset request values."""
    return {key: value for key, value in values.items() if value is not None}
