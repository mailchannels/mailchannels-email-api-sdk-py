"""Send messages with MailChannels attachment helpers."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import mailchannels

logger = logging.getLogger(__name__)


def build_attachment_message(path: str | Path) -> dict[str, Any]:
    """Build an email payload with a local file attachment."""
    file_path = Path(path)
    logger.info("Building attachment example message path=%s", file_path)
    return {
        "from": {"email": "sender@example.com"},
        "to": [{"email": "recipient@example.net"}],
        "subject": "Attachment example",
        "text": "The requested file is attached.",
        "attachments": [
            mailchannels.Attachment.from_bytes(
                file_path.read_bytes(),
                filename=file_path.name,
            ),
        ],
    }


def queue_attachment(client: mailchannels.Client, path: str | Path) -> dict[str, Any]:
    """Queue an email with a local file attachment."""
    return client.emails.queue(build_attachment_message(path))


def main() -> None:
    """Run the attachment example from environment configuration."""
    client = mailchannels.Client(api_key=os.environ["MAILCHANNELS_API_KEY"])
    result = queue_attachment(client, os.environ["ATTACHMENT_PATH"])
    print(result)


if __name__ == "__main__":
    main()
