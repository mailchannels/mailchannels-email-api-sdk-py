"""Tests for webhook resources and helpers."""

from __future__ import annotations

import base64
import hashlib
import logging

import pytest
from conftest import FakeHTTPXClient, FakeRequestsClient
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

import mailchannels
from mailchannels.client import Client
from mailchannels.exceptions import (
    ConflictError,
    InvalidRequestError,
    NotFoundError,
    ResponseValidationError,
    ServerError,
)
from mailchannels.response import EmptyResponse, SDKResponse
from mailchannels.version import user_agent
from mailchannels.webhooks import (
    parse_signature_input,
    signature_is_fresh,
    signature_key_id,
    verify_content_digest,
    verify_webhook_signature,
)
from mailchannels.webhooks.webhooks import _masked_endpoint


def test_webhook_management_uses_documented_paths() -> None:
    """It manages webhook endpoints through the documented resource."""
    transport = FakeRequestsClient(SDKResponse(201, None, ""))
    client = Client(api_key="test-key", http_client=transport)

    client.webhooks.create("https://example.com/mailchannels")
    client.webhooks.list()
    client.webhooks.delete_all()
    client.webhooks.validate(request_id="test_request_1")

    assert [call["method"] for call in transport.calls] == [
        "POST",
        "GET",
        "DELETE",
        "POST",
    ]
    assert [call["url"] for call in transport.calls] == [
        "https://api.example.test/tx/v1/webhook",
        "https://api.example.test/tx/v1/webhook",
        "https://api.example.test/tx/v1/webhook",
        "https://api.example.test/tx/v1/webhook/validate",
    ]
    assert transport.calls[0]["params"] == {
        "endpoint": "https://example.com/mailchannels"
    }
    assert transport.calls[0]["json"] is None
    assert transport.calls[3]["json"] == {"request_id": "test_request_1"}


ENDPOINT = "https://example.com/mailchannels?tenant=a b&x=1"


@pytest.mark.parametrize("failure_threshold", [0, 1, 5, 10_000])
def test_webhook_create_sends_failure_threshold_in_body(
    failure_threshold: int,
) -> None:
    """It sends the optional failure threshold as the enrollment JSON body."""
    transport = FakeRequestsClient(SDKResponse(204, None, ""))
    client = Client(api_key="test-key", http_client=transport)

    client.webhooks.create(ENDPOINT, failure_threshold=failure_threshold)

    assert transport.calls[0]["method"] == "POST"
    assert transport.calls[0]["url"] == "https://api.example.test/tx/v1/webhook"
    assert transport.calls[0]["params"] == {"endpoint": ENDPOINT}
    assert transport.calls[0]["json"] == {"failure_threshold": failure_threshold}


def test_webhook_create_accepts_201_when_threshold_was_not_set() -> None:
    """It treats the enrolled-without-threshold 201 response as success."""
    transport = FakeRequestsClient(SDKResponse(201, None, "", {"X-Request-Id": "r1"}))
    client = Client(api_key="test-key", http_client=transport)

    result = client.webhooks.create(ENDPOINT, failure_threshold=3)

    assert result == {"http_headers": {"X-Request-Id": "r1"}}


def test_webhook_create_already_enrolled_raises_conflict() -> None:
    """It surfaces an existing enrollment as ConflictError."""
    transport = FakeRequestsClient(SDKResponse(409, None, ""))
    client = Client(api_key="test-key", http_client=transport)

    with pytest.raises(ConflictError):
        client.webhooks.create(ENDPOINT, failure_threshold=3)


@pytest.mark.parametrize("failure_threshold", [1, 5, 10_000])
def test_webhook_update_patches_failure_threshold(failure_threshold: int) -> None:
    """It updates webhook settings through PATCH /webhook."""
    transport = FakeRequestsClient(SDKResponse(204, None, ""))
    client = Client(api_key="test-key", http_client=transport)

    result = client.webhooks.update(ENDPOINT, failure_threshold=failure_threshold)

    assert result == {"http_headers": {}}
    assert transport.calls == [
        {
            "method": "PATCH",
            "url": "https://api.example.test/tx/v1/webhook",
            "headers": {
                "Content-Type": "application/json",
                "User-Agent": user_agent(),
                "X-API-Key": "test-key",
            },
            "json": {"failure_threshold": failure_threshold},
            "params": {"endpoint": ENDPOINT},
        }
    ]


def test_webhook_delete_failure_threshold_uses_documented_path() -> None:
    """It removes the threshold through DELETE /webhook/failure-threshold."""
    transport = FakeRequestsClient(SDKResponse(204, None, ""))
    client = Client(api_key="test-key", http_client=transport)

    result = client.webhooks.delete_failure_threshold(ENDPOINT)

    assert result == {"http_headers": {}}
    assert transport.calls == [
        {
            "method": "DELETE",
            "url": "https://api.example.test/tx/v1/webhook/failure-threshold",
            "headers": {
                "Content-Type": "application/json",
                "User-Agent": user_agent(),
                "X-API-Key": "test-key",
            },
            "json": None,
            "params": {"endpoint": ENDPOINT},
        }
    ]


@pytest.mark.parametrize(
    ("status_code", "error_class"),
    [
        (400, InvalidRequestError),
        (404, NotFoundError),
        (500, ServerError),
    ],
)
def test_webhook_threshold_operations_raise_typed_errors(
    status_code: int,
    error_class: type[Exception],
) -> None:
    """It maps documented error statuses for update and threshold removal."""
    transport = FakeRequestsClient(SDKResponse(status_code, None, ""))
    client = Client(api_key="test-key", http_client=transport)

    with pytest.raises(error_class):
        client.webhooks.update(ENDPOINT, failure_threshold=0)
    with pytest.raises(error_class):
        client.webhooks.delete_failure_threshold("")

    assert transport.calls[0]["json"] == {"failure_threshold": 0}
    assert transport.calls[1]["params"] == {"endpoint": ""}


def test_webhook_strict_responses_for_threshold_operations() -> None:
    """It returns typed models for threshold operations in strict mode."""
    transport = FakeRequestsClient(SDKResponse(204, None, "", {"X-Request-Id": "r1"}))
    client = Client(api_key="test-key", http_client=transport, strict_responses=True)

    created = client.webhooks.create(ENDPOINT, failure_threshold=2)
    updated = client.webhooks.update(ENDPOINT, failure_threshold=3)
    deleted = client.webhooks.delete_failure_threshold(ENDPOINT)

    for result in (created, updated, deleted):
        assert isinstance(result, EmptyResponse)
        assert result.http_headers == {"X-Request-Id": "r1"}


def test_webhook_strict_list_exposes_failure_threshold() -> None:
    """It parses set, null, and absent failure thresholds from GET /webhook."""
    transport = FakeRequestsClient(
        SDKResponse(
            200,
            [
                {"webhook": "https://example.com/a", "failure_threshold": 5},
                {"webhook": "https://example.com/b", "failure_threshold": None},
                {"webhook": "https://example.com/c"},
            ],
            "[]",
        )
    )
    client = Client(api_key="test-key", http_client=transport, strict_responses=True)

    result = client.webhooks.list()

    assert [item.failure_threshold for item in result.data] == [5, None, None]


def test_webhook_strict_list_rejects_non_integer_failure_threshold() -> None:
    """It rejects a malformed failure threshold in strict mode."""
    transport = FakeRequestsClient(
        SDKResponse(
            200,
            [{"webhook": "https://example.com/a", "failure_threshold": "many"}],
            "[]",
        )
    )
    client = Client(api_key="test-key", http_client=transport, strict_responses=True)

    with pytest.raises(ResponseValidationError):
        client.webhooks.list()


def test_webhook_threshold_operations_log_at_info(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """It logs webhook setting mutations at info level."""
    transport = FakeRequestsClient(SDKResponse(204, None, ""))
    client = Client(api_key="test-key", http_client=transport)

    with caplog.at_level(logging.INFO, logger="mailchannels.webhooks.webhooks"):
        client.webhooks.create(ENDPOINT, failure_threshold=2)
        client.webhooks.update(ENDPOINT, failure_threshold=3)
        client.webhooks.delete_failure_threshold(ENDPOINT)

    records = [
        record
        for record in caplog.records
        if record.name == "mailchannels.webhooks.webhooks"
        and record.levelno == logging.INFO
    ]
    assert len(records) == 3


SECRET_ENDPOINT = "https://user:pw@Hooks.Example.com:8443/in/path-token?token=SECRET#frag"


async def test_webhook_logs_never_include_endpoint_credentials(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """It logs only the scheme and host of webhook endpoints, sync and async."""
    client = Client(
        api_key="test-key",
        http_client=FakeRequestsClient(SDKResponse(204, None, "")),
        async_http_client=FakeHTTPXClient(SDKResponse(204, None, "")),
    )

    with caplog.at_level(logging.DEBUG, logger="mailchannels.webhooks.webhooks"):
        client.webhooks.create(SECRET_ENDPOINT, failure_threshold=2)
        client.webhooks.update(SECRET_ENDPOINT, failure_threshold=3)
        client.webhooks.delete_failure_threshold(SECRET_ENDPOINT)
        await client.webhooks.create_async(SECRET_ENDPOINT)
        await client.webhooks.update_async(SECRET_ENDPOINT, failure_threshold=3)
        await client.webhooks.delete_failure_threshold_async(SECRET_ENDPOINT)

    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "mailchannels.webhooks.webhooks"
    ]
    assert len(messages) == 6
    for message in messages:
        assert "endpoint=https://hooks.example.com:8443" in message
        for secret in ("SECRET", "path-token", "user", "pw", "frag"):
            assert secret not in message


@pytest.mark.parametrize(
    ("endpoint", "masked"),
    [
        ("https://example.com", "https://example.com"),
        ("https://example.com/hook?token=abc", "https://example.com"),
        ("  HTTPS://Example.COM/Hook  ", "https://example.com"),
        ("http://user:pw@example.com:8080/x", "http://example.com:8080"),
        ("https://[2001:db8::1]:8443/x?k=v", "https://[2001:db8::1]:8443"),
        ("https://b\u00fccher.example/\u00fc?k=\u00fc", "https://b\u00fccher.example"),
        ("https://example.com:notaport/x?token=abc", "unparseable endpoint"),
        ("https://[::1/x?token=abc", "unparseable endpoint"),
        ("example.com/hook?token=abc", "unparseable endpoint"),
        ("token-only-secret", "unparseable endpoint"),
        ("https:///path?token=abc", "unparseable endpoint"),
        ("", "unparseable endpoint"),
    ],
)
def test_masked_endpoint_keeps_only_scheme_and_host(endpoint: str, masked: str) -> None:
    """It reduces any endpoint, valid or malformed, to a credential-free form."""
    assert _masked_endpoint(endpoint) == masked


async def test_webhook_threshold_async_methods_use_async_transport() -> None:
    """It exposes async enrollment, update, and threshold removal."""
    transport = FakeHTTPXClient(SDKResponse(204, None, ""))
    client = Client(api_key="test-key", async_http_client=transport)

    await client.webhooks.create_async(ENDPOINT)
    await client.webhooks.create_async(ENDPOINT, failure_threshold=2)
    await client.webhooks.update_async(ENDPOINT, failure_threshold=3)
    await client.webhooks.delete_failure_threshold_async(ENDPOINT)

    assert [
        (call["method"], call["url"].removeprefix("https://api.example.test/tx/v1"))
        for call in transport.calls
    ] == [
        ("POST", "/webhook"),
        ("POST", "/webhook"),
        ("PATCH", "/webhook"),
        ("DELETE", "/webhook/failure-threshold"),
    ]
    assert [call["json"] for call in transport.calls] == [
        None,
        {"failure_threshold": 2},
        {"failure_threshold": 3},
        None,
    ]
    assert all(call["params"] == {"endpoint": ENDPOINT} for call in transport.calls)


async def test_webhook_threshold_async_errors_raise_not_found() -> None:
    """It raises NotFoundError from async calls for an unknown endpoint."""
    transport = FakeHTTPXClient(SDKResponse(404, None, ""))
    client = Client(api_key="test-key", async_http_client=transport)

    with pytest.raises(NotFoundError):
        await client.webhooks.update_async(ENDPOINT, failure_threshold=3)
    with pytest.raises(NotFoundError):
        await client.webhooks.delete_failure_threshold_async(ENDPOINT)


async def test_webhook_module_level_threshold_operations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """It exposes threshold operations on the module-level Webhooks namespace."""
    transport = FakeRequestsClient(SDKResponse(204, None, ""))
    async_transport = FakeHTTPXClient(SDKResponse(204, None, ""))
    monkeypatch.setattr(mailchannels, "api_key", "module-key")
    monkeypatch.setattr(mailchannels, "default_http_client", transport)
    monkeypatch.setattr(mailchannels, "default_async_http_client", async_transport)

    mailchannels.Webhooks.create(ENDPOINT)
    mailchannels.Webhooks.create(ENDPOINT, failure_threshold=2)
    mailchannels.Webhooks.update(ENDPOINT, failure_threshold=3)
    mailchannels.Webhooks.delete_failure_threshold(ENDPOINT)
    await mailchannels.Webhooks.create_async(ENDPOINT)
    await mailchannels.Webhooks.create_async(ENDPOINT, failure_threshold=2)
    await mailchannels.Webhooks.update_async(ENDPOINT, failure_threshold=3)
    await mailchannels.Webhooks.delete_failure_threshold_async(ENDPOINT)

    expected = [
        ("POST", None),
        ("POST", {"failure_threshold": 2}),
        ("PATCH", {"failure_threshold": 3}),
        ("DELETE", None),
    ]
    for calls in (transport.calls, async_transport.calls):
        assert [(call["method"], call["json"]) for call in calls] == expected
        assert all(call["params"] == {"endpoint": ENDPOINT} for call in calls)
        assert all(call["headers"]["X-API-Key"] == "module-key" for call in calls)


def test_webhook_batches_public_key_and_resend() -> None:
    """It exposes webhook batch, public-key, and resend endpoints."""
    transport = FakeRequestsClient(SDKResponse(200, {"ok": True}, "{}"))
    client = Client(api_key="test-key", http_client=transport)

    client.webhooks.batches(statuses=["4xx", "5xx"], limit=25, offset=5)
    client.webhooks.public_key("mckey")
    client.webhooks.resend_batch(123)

    assert transport.calls[0]["url"] == (
        "https://api.example.test/tx/v1/webhook-batch"
    )
    assert transport.calls[0]["params"] == {
        "statuses": "4xx,5xx",
        "limit": 25,
        "offset": 5,
    }
    assert "X-API-Key" not in transport.calls[1]["headers"]
    assert transport.calls[1]["url"] == (
        "https://api.example.test/tx/v1/webhook/public-key"
    )
    assert transport.calls[1]["params"] == {"id": "mckey"}
    assert transport.calls[2]["url"] == (
        "https://api.example.test/tx/v1/webhook-batch/123/resend"
    )
    assert transport.calls[2]["headers"] == {
        "Content-Type": "application/json",
        "User-Agent": user_agent(),
        "X-API-Key": "test-key",
    }


def test_webhook_resend_batch_path_variable_is_url_encoded() -> None:
    """It encodes webhook batch IDs in resend paths."""
    transport = FakeRequestsClient(SDKResponse(200, {"ok": True}, "{}"))
    client = Client(api_key="test-key", http_client=transport)

    client.webhooks.resend_batch("123/456?x=1")

    assert transport.calls[0]["url"] == (
        "https://api.example.test/tx/v1/webhook-batch/"
        "123%2F456%3Fx%3D1/resend"
    )


def test_webhook_resend_batch_unknown_id_raises_not_found() -> None:
    """It surfaces a missing webhook batch as NotFoundError, not InvalidRequestError."""
    transport = FakeRequestsClient(
        SDKResponse(404, {"message": "Batch not found"}, "Batch not found"),
    )
    client = Client(api_key="test-key", http_client=transport)

    with pytest.raises(NotFoundError) as error:
        client.webhooks.resend_batch(999)

    assert error.value.status_code == 404
    assert error.value.error_type == "not_found"


def test_webhook_destructive_operations_log_at_info(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """It logs intentional webhook mutations at info level."""
    transport = FakeRequestsClient(SDKResponse(200, {"ok": True}, "{}"))
    client = Client(api_key="test-key", http_client=transport)

    with caplog.at_level(logging.INFO, logger="mailchannels.webhooks.webhooks"):
        client.webhooks.delete_all()
        client.webhooks.resend_batch(123)

    records = [
        record
        for record in caplog.records
        if record.name == "mailchannels.webhooks.webhooks"
    ]
    assert [record.levelno for record in records] == [logging.INFO, logging.INFO]


async def test_webhook_async_methods_use_async_transport() -> None:
    """It exposes async webhook operations."""
    transport = FakeHTTPXClient(SDKResponse(200, {"webhook_batches": []}, "{}"))
    client = Client(api_key="test-key", async_http_client=transport)

    await client.webhooks.batches_async(statuses=["no_response"])
    await client.webhooks.resend_batch_async("123/456?x=1")

    assert transport.calls[0]["method"] == "GET"
    assert transport.calls[0]["params"] == {"statuses": "no_response"}
    assert transport.calls[1]["url"] == (
        "https://api.example.test/tx/v1/webhook-batch/"
        "123%2F456%3Fx%3D1/resend"
    )


def test_webhook_signature_helpers() -> None:
    """It parses signature metadata and verifies the content digest."""
    body = b'[{"event":"delivered","customer_handle":"customer_123"}]'
    digest = base64.b64encode(hashlib.sha256(body).digest()).decode("ascii")
    headers = {
        "Content-Digest": f"sha-256=:{digest}:",
        "Signature-Input": (
            'sig_1738775282=("content-digest");created=1738868393;'
            'alg="ed25519";keyid="mckey"'
        ),
    }

    parameters = parse_signature_input(headers["Signature-Input"])

    assert parameters.signature_name == "sig_1738775282"
    assert parameters.covered_components == ["content-digest"]
    assert parameters.algorithm == "ed25519"
    assert parameters.key_id == "mckey"
    assert signature_key_id(headers) == "mckey"
    assert signature_is_fresh(parameters, now=1738868400)
    assert verify_content_digest(headers, body)


def test_webhook_signature_verification_accepts_valid_ed25519_signature() -> None:
    """It verifies a complete MailChannels webhook signature."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw,
    )
    body = b'[{"event":"delivered","customer_handle":"customer_123"}]'
    digest = base64.b64encode(hashlib.sha256(body).digest()).decode("ascii")
    signature_input = (
        'sig=("content-digest");created=1738868393;alg="ed25519";keyid="mckey"'
    )
    signature_base = (
        f'"content-digest": sha-256=:{digest}:\n'
        f'"@signature-params": {signature_input.split("=", maxsplit=1)[1]}'
    ).encode()
    signature = base64.b64encode(private_key.sign(signature_base)).decode("ascii")
    headers = {
        "Content-Digest": f"sha-256=:{digest}:",
        "Signature-Input": signature_input,
        "Signature": f"sig=:{signature}:",
    }

    assert verify_webhook_signature(
        headers,
        body,
        {"key": base64.b64encode(public_key).decode("ascii")},
        now=1738868400,
    )


def test_webhooks_static_verify_accepts_public_key_model_response() -> None:
    """It exposes full signature verification from the Webhooks namespace."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw,
    )
    body = b'{"event":"processed"}'
    digest = base64.b64encode(hashlib.sha256(body).digest()).decode("ascii")
    signature_input = 'sig=("content-digest");created=10;keyid="mckey"'
    signature_base = (
        f'"content-digest": sha-256=:{digest}:\n'
        f'"@signature-params": {signature_input.split("=", maxsplit=1)[1]}'
    ).encode()
    signature = base64.b64encode(private_key.sign(signature_base)).decode("ascii")
    headers = {
        "content-digest": f"sha-256=:{digest}:",
        "signature-input": signature_input,
        "signature": f"sig=:{signature}:",
    }

    assert Client(api_key="test-key").webhooks.verify(
        headers,
        body,
        base64.b64encode(public_key).decode("ascii"),
        now=12,
    )


def test_webhook_content_digest_missing_header_returns_false() -> None:
    """It rejects webhook requests without a Content-Digest header."""
    assert not verify_content_digest({}, b"{}")


def test_webhook_signature_verification_rejects_bad_signature() -> None:
    """It rejects forged webhook signatures even when the digest matches."""
    private_key = Ed25519PrivateKey.generate()
    other_key = Ed25519PrivateKey.generate().public_key().public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw,
    )
    body = b"{}"
    digest = base64.b64encode(hashlib.sha256(body).digest()).decode("ascii")
    signature_input = 'sig=("content-digest");created=10;keyid="mckey"'
    signature_base = (
        f'"content-digest": sha-256=:{digest}:\n'
        f'"@signature-params": {signature_input.split("=", maxsplit=1)[1]}'
    ).encode()
    signature = base64.b64encode(private_key.sign(signature_base)).decode("ascii")

    assert not verify_webhook_signature(
        {
            "Content-Digest": f"sha-256=:{digest}:",
            "Signature-Input": signature_input,
            "Signature": f"sig=:{signature}:",
        },
        body,
        base64.b64encode(other_key).decode("ascii"),
        now=12,
    )


def test_webhook_signature_verification_rejects_missing_signature_header() -> None:
    """It rejects requests that only include a matching content digest."""
    body = b"{}"
    digest = base64.b64encode(hashlib.sha256(body).digest()).decode("ascii")

    assert not verify_webhook_signature(
        {
            "Content-Digest": f"sha-256=:{digest}:",
            "Signature-Input": 'sig=("content-digest");created=10;keyid="mckey"',
        },
        body,
        "x" * 44,
        now=12,
    )


def test_webhook_content_digest_wrong_digest_returns_false() -> None:
    """It rejects webhook bodies that do not match the supplied digest."""
    digest = base64.b64encode(hashlib.sha256(b"expected").digest()).decode("ascii")

    assert not verify_content_digest({"Content-Digest": f"sha-256=:{digest}:"}, b"bad")


@pytest.mark.parametrize(
    "digest_header",
    [
        "sha-512=:abc:",
        "sha-256=abc",
        "not-a-digest",
    ],
)
def test_webhook_content_digest_malformed_header_returns_false(
    digest_header: str,
) -> None:
    """It rejects malformed Content-Digest headers without crashing."""
    assert not verify_content_digest({"Content-Digest": digest_header}, b"{}")


def test_webhook_content_digest_non_base64_returns_false() -> None:
    """It rejects invalid base64 digest values without crashing."""
    assert not verify_content_digest({"Content-Digest": "sha-256=:%%%%:"}, b"{}")


def test_webhook_content_digest_header_lookup_is_case_insensitive() -> None:
    """It accepts case variations in webhook digest headers."""
    body = b'{"event":"delivered"}'
    digest = base64.b64encode(hashlib.sha256(body).digest()).decode("ascii")

    assert verify_content_digest({"content-digest": f"sha-256=:{digest}:"}, body)


def test_webhook_signature_key_id_missing_header_returns_none() -> None:
    """It returns None when Signature-Input is absent."""
    assert signature_key_id({}) is None


def test_webhook_signature_key_id_header_lookup_is_case_insensitive() -> None:
    """It accepts case variations in webhook signature headers."""
    headers = {
        "signature-input": (
            'sig=("content-digest");created=1738868393;'
            'alg="ed25519";keyid="mckey"'
        )
    }

    assert signature_key_id(headers) == "mckey"


def test_webhook_signature_key_id_malformed_header_raises_value_error() -> None:
    """It raises ValueError for malformed Signature-Input headers."""
    with pytest.raises(ValueError):
        signature_key_id({"Signature-Input": "not a structured signature input"})


def test_webhook_signature_missing_created_is_not_fresh() -> None:
    """It treats signatures without created timestamps as stale."""
    parameters = parse_signature_input('sig=("content-digest");keyid="mckey"')

    assert parameters.created is None
    assert not signature_is_fresh(parameters, now=1738868400)


def test_webhook_signature_created_outside_tolerance_is_not_fresh() -> None:
    """It rejects signatures older than the allowed tolerance."""
    parameters = parse_signature_input(
        'sig=("content-digest");created=1738860000;keyid="mckey"'
    )

    assert not signature_is_fresh(parameters, now=1738868400, tolerance_seconds=300)


def test_webhook_signature_tolerance_alias_controls_max_age() -> None:
    """It keeps tolerance_seconds as a compatibility alias for max age."""
    parameters = parse_signature_input(
        'sig=("content-digest");created=1738868000;keyid="mckey"'
    )

    assert not signature_is_fresh(parameters, now=1738868400)
    assert signature_is_fresh(parameters, now=1738868400, tolerance_seconds=500)


def test_webhook_signature_small_future_skew_is_fresh() -> None:
    """It accepts a small forward clock skew."""
    parameters = parse_signature_input(
        'sig=("content-digest");created=1738868425;keyid="mckey"'
    )

    assert signature_is_fresh(parameters, now=1738868400)


def test_webhook_signature_future_within_age_but_outside_skew_is_not_fresh() -> None:
    """It rejects future signatures even when inside the stale-age window."""
    parameters = parse_signature_input(
        'sig=("content-digest");created=1738868460;keyid="mckey"'
    )

    assert not signature_is_fresh(parameters, now=1738868400)
    assert signature_is_fresh(
        parameters,
        now=1738868400,
        max_skew_seconds=60,
    )


def test_webhook_signature_future_created_outside_tolerance_is_not_fresh() -> None:
    """It rejects signatures created too far in the future."""
    parameters = parse_signature_input(
        'sig=("content-digest");created=1738872000;keyid="mckey"'
    )

    assert not signature_is_fresh(parameters, now=1738868400, tolerance_seconds=300)
