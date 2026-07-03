"""Tests for custom tracking domain resources."""

from __future__ import annotations

import logging

import pytest
from conftest import FakeHTTPXClient, FakeRequestsClient

import mailchannels
from mailchannels.client import Client
from mailchannels.custom_tracking_domains.types import CustomTrackingDomainResult
from mailchannels.response import SDKResponse


def _domain(name: str = "newsletter") -> dict[str, object]:
    """Build a valid registered custom tracking domain response body."""
    return {
        "name": name,
        "hostname": "click.example.com",
        "scope": "click",
        "status": "active",
        "created_at": "2026-07-01T00:00:00Z",
    }


def _dns_setup_required() -> dict[str, object]:
    """Build a valid pending DNS verification response body."""
    return {
        "instructions": "Add the TXT and CNAME records, then retry.",
        "token": "550e8400-e29b-41d4-a716-446655440000",
        "txt_record_name": "_mailchannels-verify.click.example.com",
        "txt_record_value": "550e8400-e29b-41d4-a716-446655440000",
    }


def test_list_custom_tracking_domains_uses_filters() -> None:
    """It retrieves custom tracking domains with optional filters."""
    transport = FakeRequestsClient(
        SDKResponse(200, {"custom_tracking_domains": [], "total": 0}, "{}")
    )
    client = Client(api_key="test-key", http_client=transport)

    client.custom_tracking_domains.list(
        name="newsletter",
        status="active",
        scope="click",
        limit=10,
        offset=0,
    )

    assert transport.calls[0]["method"] == "GET"
    assert transport.calls[0]["url"] == (
        "https://api.example.test/tx/v1/custom-tracking-domains"
    )
    assert transport.calls[0]["params"] == {
        "name": "newsletter",
        "status": "active",
        "scope": "click",
        "limit": 10,
        "offset": 0,
    }


def test_create_custom_tracking_domain_uses_expected_path_and_payload() -> None:
    """It registers a custom tracking domain."""
    transport = FakeRequestsClient(SDKResponse(201, _domain(), "{}"))
    client = Client(api_key="test-key", http_client=transport)

    result = client.custom_tracking_domains.create(
        name="newsletter",
        hostname="click.example.com",
        scope="click",
    )

    assert result["hostname"] == "click.example.com"
    assert transport.calls[0]["method"] == "POST"
    assert transport.calls[0]["url"] == (
        "https://api.example.test/tx/v1/custom-tracking-domains"
    )
    assert transport.calls[0]["json"] == {
        "name": "newsletter",
        "hostname": "click.example.com",
        "scope": "click",
    }


def test_create_custom_tracking_domain_accepts_pending_dns_setup_response() -> None:
    """It surfaces a 202 DNS-verification-pending response as a normal result."""
    transport = FakeRequestsClient(SDKResponse(202, _dns_setup_required(), "{}"))
    client = Client(api_key="test-key", http_client=transport, strict_responses=True)

    result = client.custom_tracking_domains.create(
        name="newsletter",
        hostname="click.example.com",
        scope="click",
    )

    assert isinstance(result, CustomTrackingDomainResult)
    assert result.status is None
    assert result.instructions == "Add the TXT and CNAME records, then retry."
    assert result.token == "550e8400-e29b-41d4-a716-446655440000"


def test_create_pending_dns_result_omits_instructions() -> None:
    """It accepts a pending response that only carries TXT record fields."""
    transport = FakeRequestsClient(
        SDKResponse(
            202,
            {
                "token": "550e8400-e29b-41d4-a716-446655440000",
                "txt_record_name": "_mailchannels-verify.click.example.com",
                "txt_record_value": "550e8400-e29b-41d4-a716-446655440000",
            },
            "{}",
        )
    )
    client = Client(api_key="test-key", http_client=transport, strict_responses=True)

    result = client.custom_tracking_domains.create(
        name="newsletter",
        hostname="click.example.com",
        scope="click",
    )

    assert isinstance(result, CustomTrackingDomainResult)
    assert result.instructions is None
    assert result.token == "550e8400-e29b-41d4-a716-446655440000"


def test_custom_tracking_domain_result_rejects_empty_response() -> None:
    """It rejects a response that matches neither the created nor pending shape."""
    with pytest.raises(ValueError, match="registered domain or a pending"):
        CustomTrackingDomainResult.model_validate({})


def test_create_raises_invalid_request_for_incomplete_dns() -> None:
    """A 422 (DNS records still not in place) raises InvalidRequestError."""
    transport = FakeRequestsClient(SDKResponse(422, _dns_setup_required(), "{}"))
    client = Client(api_key="test-key", http_client=transport)

    with pytest.raises(mailchannels.InvalidRequestError) as excinfo:
        client.custom_tracking_domains.create(
            name="newsletter",
            hostname="click.example.com",
            scope="click",
        )

    assert excinfo.value.response["instructions"] == (
        "Add the TXT and CNAME records, then retry."
    )


def test_update_raises_invalid_request_for_incomplete_dns() -> None:
    """A 422 on re-activation (DNS still incomplete) raises InvalidRequestError."""
    transport = FakeRequestsClient(SDKResponse(422, _dns_setup_required(), "{}"))
    client = Client(api_key="test-key", http_client=transport)

    with pytest.raises(mailchannels.InvalidRequestError) as excinfo:
        client.custom_tracking_domains.update(
            "click.example.com",
            "click",
            status="active",
        )

    assert excinfo.value.response["instructions"] == (
        "Add the TXT and CNAME records, then retry."
    )


def test_update_custom_tracking_domain_accepts_pending_dns_setup_response() -> None:
    """It surfaces a 202 re-activation-pending response as a normal result."""
    transport = FakeRequestsClient(SDKResponse(202, _dns_setup_required(), "{}"))
    client = Client(api_key="test-key", http_client=transport, strict_responses=True)

    result = client.custom_tracking_domains.update(
        "click.example.com",
        "click",
        status="active",
    )

    assert isinstance(result, CustomTrackingDomainResult)
    assert result.status is None
    assert result.instructions == "Add the TXT and CNAME records, then retry."


def test_update_and_delete_custom_tracking_domains_use_documented_paths() -> None:
    """It updates and deletes custom tracking domains using the OpenAPI paths."""
    transport = FakeRequestsClient(SDKResponse(200, _domain(), "{}"))
    client = Client(api_key="test-key", http_client=transport)

    client.custom_tracking_domains.update(
        "click.example.com",
        "click",
        name="newsletter2",
        status="disabled",
    )

    delete_transport = FakeRequestsClient(SDKResponse(204, None, ""))
    delete_client = Client(api_key="test-key", http_client=delete_transport)
    delete_client.custom_tracking_domains.delete("click.example.com", "click")

    assert transport.calls[0]["method"] == "PATCH"
    assert transport.calls[0]["url"] == (
        "https://api.example.test/tx/v1/custom-tracking-domains/"
        "click.example.com/click"
    )
    assert transport.calls[0]["json"] == {
        "name": "newsletter2",
        "status": "disabled",
    }
    assert delete_transport.calls[0]["method"] == "DELETE"
    assert delete_transport.calls[0]["url"] == (
        "https://api.example.test/tx/v1/custom-tracking-domains/"
        "click.example.com/click"
    )


def test_custom_tracking_domain_path_variables_are_url_encoded() -> None:
    """It encodes hostname and scope values in custom tracking domain paths."""
    transport = FakeRequestsClient(SDKResponse(204, None, ""))
    client = Client(api_key="test-key", http_client=transport)

    client.custom_tracking_domains.delete("example.com/path?x=1", "click")

    assert transport.calls[0]["url"] == (
        "https://api.example.test/tx/v1/custom-tracking-domains/"
        "example.com%2Fpath%3Fx%3D1/click"
    )


def test_custom_tracking_domains_mutations_log_at_info(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """It logs intentional custom tracking domain mutations at info level."""
    transport = FakeRequestsClient(SDKResponse(204, None, ""))
    client = Client(api_key="test-key", http_client=transport)

    logger_name = "mailchannels.custom_tracking_domains.custom_tracking_domains"
    with caplog.at_level(logging.INFO, logger=logger_name):
        client.custom_tracking_domains.update(
            "click.example.com",
            "click",
            status="disabled",
        )
        client.custom_tracking_domains.delete("click.example.com", "click")

    records = [record for record in caplog.records if record.name == logger_name]
    assert [record.levelno for record in records] == [
        logging.INFO,
        logging.INFO,
    ]


def test_module_level_custom_tracking_domains_api_uses_global_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """It supports module-level custom tracking domain calls."""
    transport = FakeRequestsClient(
        SDKResponse(200, {"custom_tracking_domains": [], "total": 0}, "{}")
    )
    monkeypatch.setattr(mailchannels, "api_key", "module-key")
    monkeypatch.setattr(mailchannels, "default_http_client", transport)

    mailchannels.CustomTrackingDomains.list()

    assert transport.calls[0]["headers"]["X-API-Key"] == "module-key"
    assert transport.calls[0]["url"] == (
        "https://api.example.test/tx/v1/custom-tracking-domains"
    )


async def test_custom_tracking_domains_async_methods_use_async_transport() -> None:
    """It exposes async custom tracking domain operations."""
    transport = FakeHTTPXClient(SDKResponse(200, _domain(), "{}"))
    client = Client(api_key="test-key", async_http_client=transport)

    await client.custom_tracking_domains.create_async(
        name="newsletter",
        hostname="click.example.com",
        scope="click",
    )
    await client.custom_tracking_domains.update_async(
        "click.example.com/path",
        "click",
        status="active",
    )

    assert transport.calls[0]["method"] == "POST"
    assert transport.calls[1]["url"] == (
        "https://api.example.test/tx/v1/custom-tracking-domains/"
        "click.example.com%2Fpath/click"
    )


async def test_custom_tracking_domains_list_and_delete_async_parse_responses() -> None:
    """It parses strict list and delete responses over the async transport."""
    list_transport = FakeHTTPXClient(
        SDKResponse(200, {"custom_tracking_domains": [_domain()], "total": 1}, "{}")
    )
    list_client = Client(
        api_key="test-key",
        async_http_client=list_transport,
        strict_responses=True,
    )

    list_result = await list_client.custom_tracking_domains.list_async(status="active")

    assert list_result.total == 1
    assert list_result.custom_tracking_domains[0].hostname == "click.example.com"
    assert list_transport.calls[0]["method"] == "GET"

    delete_transport = FakeHTTPXClient(SDKResponse(204, None, ""))
    delete_client = Client(
        api_key="test-key",
        async_http_client=delete_transport,
        strict_responses=True,
    )

    delete_result = await delete_client.custom_tracking_domains.delete_async(
        "click.example.com",
        "click",
    )

    assert isinstance(delete_result, mailchannels.EmptyResponse)
    assert delete_transport.calls[0]["method"] == "DELETE"
