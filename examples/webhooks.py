"""Configure and verify MailChannels webhooks."""

from __future__ import annotations

import logging
import os
from typing import Any

import mailchannels

logger = logging.getLogger(__name__)


def configure_webhook(
    client: mailchannels.Client,
    endpoint: str,
    failure_threshold: int | None = None,
) -> dict[str, Any]:
    """Enroll an endpoint, optionally alerting after consecutive failures."""
    logger.info(
        "Configuring example webhook failure_threshold=%s",
        failure_threshold,
    )
    return client.webhooks.create(endpoint, failure_threshold=failure_threshold)


def set_failure_threshold(
    client: mailchannels.Client,
    endpoint: str,
    failure_threshold: int,
) -> dict[str, Any]:
    """Change how many consecutive failures trigger an alert for a webhook."""
    logger.info(
        "Setting example webhook failure threshold failure_threshold=%s",
        failure_threshold,
    )
    return client.webhooks.update(endpoint, failure_threshold=failure_threshold)


def disable_failure_alerts(
    client: mailchannels.Client,
    endpoint: str,
) -> dict[str, Any]:
    """Remove a webhook's failure threshold while keeping it enrolled."""
    logger.info("Disabling example webhook failure alerts")
    return client.webhooks.delete_failure_threshold(endpoint)


def failure_thresholds(client: mailchannels.Client) -> dict[str, int | None]:
    """Return the failure threshold of each enrolled webhook, keyed by stored URL.

    MailChannels stores a canonical form of the URL, so the keys can differ
    from the URL that was enrolled. Expects a client with dict responses, not
    `strict_responses=True`.
    """
    logger.info("Reading example webhook failure thresholds")
    return {
        entry["webhook"]: entry.get("failure_threshold")
        for entry in client.webhooks.list()["data"]
    }


def validate_webhooks(client: mailchannels.Client) -> dict[str, Any]:
    """Ask MailChannels to send validation events to enrolled webhooks."""
    logger.info("Validating example webhooks")
    return client.webhooks.validate(request_id="example_validation")


def inspect_failed_batches(client: mailchannels.Client) -> dict[str, Any]:
    """Retrieve webhook batches with failure-like statuses."""
    logger.info("Inspecting failed webhook batches")
    return client.webhooks.batches(statuses=["4xx", "5xx", "no_response"], limit=50)


def verify_webhook_metadata(
    headers: dict[str, str],
    body: bytes,
    public_key: str | bytes | dict[str, object],
) -> str:
    """Verify webhook authenticity and return the signing key ID."""
    parameters = mailchannels.parse_signature_input(headers["Signature-Input"])
    if not mailchannels.Webhooks.verify(headers, body, public_key):
        logger.error("MailChannels webhook signature failed verification")
        raise ValueError("Invalid MailChannels webhook signature.")
    if parameters.key_id is None:
        logger.error("MailChannels webhook signature is missing a key ID")
        raise ValueError("Missing MailChannels webhook key ID.")
    return parameters.key_id


def main() -> None:
    """Run the webhook configuration example from environment configuration."""
    client = mailchannels.Client(api_key=os.environ["MAILCHANNELS_API_KEY"])
    threshold = os.environ.get("WEBHOOK_FAILURE_THRESHOLD")
    print(
        configure_webhook(
            client,
            os.environ["WEBHOOK_ENDPOINT"],
            int(threshold) if threshold else None,
        )
    )
    print(failure_thresholds(client))


if __name__ == "__main__":
    main()
