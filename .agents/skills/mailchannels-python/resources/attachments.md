# Attachments

MailChannels expects every attachment to be Base64-encoded with a `filename`
and ideally a MIME `type`. Use `Attachment.from_bytes` — it encodes for you
and infers the MIME type from the filename.

The SDK intentionally does **not** read local files or fetch remote URLs on
your behalf. Load the bytes yourself (with the appropriate validation for
your trust boundary) and pass them in.

## From In-Memory Bytes

```python
import mailchannels

report = mailchannels.Attachment.from_bytes(
    b"<csv content>",
    filename="report.csv",
    content_type="text/csv",   # optional; inferred from filename when omitted
)
```

## From A Local File

```python
from pathlib import Path
import mailchannels

invoice = mailchannels.Attachment.from_bytes(
    Path("invoice.pdf").read_bytes(),
    filename="invoice.pdf",
)

mailchannels.Emails.queue(
    mailchannels.EmailParams(
        from_=mailchannels.EmailAddress(email="billing@example.com"),
        personalizations=[
            mailchannels.Personalization(
                to=[mailchannels.EmailAddress(email="recipient@example.net")],
            ),
        ],
        subject="Your invoice",
        content=[
            mailchannels.Content(type="text/plain", value="Your invoice is attached."),
        ],
        attachments=[invoice],
    )
)
```

Validate the path against your application's trust rules before reading —
the SDK no longer offers `Attachment.from_file()` precisely because a
generic helper cannot make that decision safely.

## From A Remote URL

```python
import requests
import mailchannels

response = requests.get("https://cdn.example.com/banner.png", timeout=30)
response.raise_for_status()
banner = mailchannels.Attachment.from_bytes(
    response.content,
    filename="banner.png",
)
```

Restrict the URL allowlist before fetching — the SDK no longer offers
`Attachment.from_url()` precisely because the unrestricted version is
vulnerable to SSRF and credential exfiltration.

## Limits

- Up to **1000 attachments** per send.
- Combined message + headers + attachments must stay under **30 MB**.
- Exceeding the size limit raises `PayloadTooLargeError` (HTTP 413).

## Raw Attachment Shape

If you ever need to construct one by hand:

```json
{
  "content": "<base64-encoded bytes>",
  "filename": "report.pdf",
  "type": "application/pdf"
}
```

`content` and `filename` are required. `type` is recommended but optional.
