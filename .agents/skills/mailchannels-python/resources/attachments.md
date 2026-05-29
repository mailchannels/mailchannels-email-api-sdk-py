# Attachments

MailChannels expects every attachment to be Base64-encoded with a `filename`
and ideally a MIME `type`. Use the `Attachment` helpers — they encode for you
and infer the MIME type.

## From A Local File

```python
import mailchannels

invoice = mailchannels.Attachment.from_file("invoice.pdf")

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

Missing files raise `MailChannelsError` with `code="AttachmentReadError"`.

## From In-Memory Bytes

```python
report = mailchannels.Attachment.from_bytes(
    b"<csv content>",
    filename="report.csv",
    content_type="text/csv",   # optional; inferred from filename when omitted
)
```

## From A Remote URL

```python
banner = mailchannels.Attachment.from_url("https://cdn.example.com/banner.png")
```

The SDK fetches and Base64-encodes the body. Failures raise `MailChannelsError`
with `code="AttachmentFetchError"`.

## Inline Images (CID References)

For images that should render inside the HTML body rather than as
downloadable attachments:

```python
logo = mailchannels.Attachment.inline_file("logo.png", content_id="company-logo")

mailchannels.Emails.queue(
    mailchannels.EmailParams(
        from_=mailchannels.EmailAddress(email="sender@example.com"),
        personalizations=[
            mailchannels.Personalization(
                to=[mailchannels.EmailAddress(email="recipient@example.net")],
            ),
        ],
        subject="Inline image",
        content=[
            mailchannels.Content(
                type="text/html",
                value="<img src='cid:company-logo' alt='Company logo'>",
            ),
        ],
        attachments=[logo],
    )
)
```

`inline_file` sets `disposition: inline` and assigns the `content_id` that
the `cid:` URL references.

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
