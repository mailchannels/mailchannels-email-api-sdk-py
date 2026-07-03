"""Manage MailChannels custom tracking domains."""

from __future__ import annotations

import logging
import os
from typing import Any

import mailchannels

logger = logging.getLogger(__name__)


def register_custom_tracking_domain(
    client: mailchannels.Client,
    name: str,
    hostname: str,
) -> dict[str, Any]:
    """Register a custom click tracking domain."""
    logger.info(
        "Registering example custom tracking domain name=%s hostname=%s",
        name,
        hostname,
    )
    return client.custom_tracking_domains.create(
        name=name,
        hostname=hostname,
        scope="click",
    )


def list_active_custom_tracking_domains(
    client: mailchannels.Client,
) -> dict[str, Any]:
    """List active custom tracking domains for every scope."""
    logger.info("Listing example custom tracking domains")
    return client.custom_tracking_domains.list(status="active")


def disable_custom_tracking_domain(
    client: mailchannels.Client,
    hostname: str,
) -> dict[str, Any]:
    """Disable a custom click tracking domain without deleting it."""
    logger.warning(
        "Disabling example custom tracking domain hostname=%s",
        hostname,
    )
    return client.custom_tracking_domains.update(hostname, "click", status="disabled")


def delete_custom_tracking_domain(
    client: mailchannels.Client,
    hostname: str,
) -> dict[str, Any]:
    """Permanently delete a custom click tracking domain."""
    logger.warning(
        "Deleting example custom tracking domain hostname=%s",
        hostname,
    )
    return client.custom_tracking_domains.delete(hostname, "click")


def main() -> None:
    """Run the custom tracking domains example from environment configuration."""
    client = mailchannels.Client(api_key=os.environ["MAILCHANNELS_API_KEY"])
    hostname = os.environ.get("MAILCHANNELS_TRACKING_HOSTNAME", "click.example.com")
    domain = register_custom_tracking_domain(client, "example-clicks", hostname)
    if domain.get("status") == "active":
        print(f"{hostname} is ready to use as {domain['name']}")
    else:
        print(domain.get("instructions"))


if __name__ == "__main__":
    main()
