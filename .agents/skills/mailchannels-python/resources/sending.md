# Sending Email

Use `Emails.queue()` (`/send-async`) as the default. Switch to `Emails.send()`
(`/send`) only when the caller specifically needs synchronous validation or
the dry-run preview.

Build payloads with the typed `EmailParams` / `Personalization` /
`Content` / `EmailAddress` Pydantic models — they validate at
construction time, narrow expected fields for the type checker, and make
AI-generated code much easier to review. The SDK also accepts plain
dictionaries (`SendParams` TypedDict, with the Resend-style `text` /
`html` shortcuts) for quick scripts, but typed models are the
recommended form.

## Quickest Send

```python
import mailchannels

mailchannels.api_key = "YOUR-API-KEY"

mailchannels.Emails.queue(
    mailchannels.EmailParams(
        from_=mailchannels.EmailAddress(email="sender@example.com", name="Sender"),
        personalizations=[
            mailchannels.Personalization(
                to=[mailchannels.EmailAddress(email="recipient@example.net")],
            ),
        ],
        subject="Hello",
        content=[
            mailchannels.Content(type="text/plain", value="Plain text body."),
            mailchannels.Content(type="text/html", value="<p>HTML body.</p>"),
        ],
    )
)
```

A few conventions worth knowing:

- `personalizations` must have at least one entry. Each
  `Personalization` must have at least one `to` recipient.
- `content` is a list of `Content` parts. Provide both `text/plain` and
  `text/html` whenever possible — receiving clients render the last
  matching part and a plain-text fallback improves deliverability.

## Per-Recipient Personalization

`Personalization` is one fully-rendered outgoing message. To fan out to
multiple recipients with per-recipient variations, give each one its
own `Personalization`:

```python
mailchannels.Emails.queue(
    mailchannels.EmailParams(
        from_=mailchannels.EmailAddress(email="sender@example.com"),
        personalizations=[
            mailchannels.Personalization(
                to=[mailchannels.EmailAddress(email="first@example.net")],
            ),
            mailchannels.Personalization(
                to=[mailchannels.EmailAddress(email="second@example.net")],
            ),
        ],
        subject="Hello",
        content=[
            mailchannels.Content(type="text/plain", value="Plain"),
            mailchannels.Content(type="text/html", value="<p>HTML</p>"),
        ],
    )
)
```

Per-recipient overrides — subject, reply-to, headers, template variables,
DKIM settings — go on each `Personalization`. The top-level `from` /
`subject` / `content` act as defaults that each personalization may
override.

## Dry Run (Send Endpoint Only)

`/send` supports `dry_run=True`. The API validates and renders the message
but does not deliver it. Useful for asserting templates render before
launch:

```python
preview = mailchannels.Emails.send(
    mailchannels.EmailParams(
        from_=mailchannels.EmailAddress(email="sender@example.com"),
        personalizations=[
            mailchannels.Personalization(
                to=[mailchannels.EmailAddress(email="recipient@example.net")],
            ),
        ],
        subject="Preview",
        content=[
            mailchannels.Content(type="text/plain", value="Body {{name}}"),
        ],
    ),
    dry_run=True,
)
# preview.data is a list of rendered messages, one per personalization.
```

`/send-async` (i.e. `Emails.queue()`) does **not** support dry-run.

## When To Pick Which

| Situation                                                                                       | Method |
|-------------------------------------------------------------------------------------------------| --- |
| Web request handler, background worker, high throughput                                         | `Emails.queue()` |
| Sending to many recipients in one call                                                          | `Emails.queue()` |
| You need the rendered message back for inspection                                               | `Emails.send(dry_run=True)` |
| You need immediate feedback on the message status to proceed, and the number of emails is small | `Emails.send()` |
| Called from `async def` code                                                                    | append `_async` to either |

## Common Pitfalls

- **Reserved headers**: Don't set `From`, `To`, `Subject`, `Reply-To`,
  `Message-ID`, `Content-Type`, `DKIM-Signature`, etc. via `headers`. Use
  the payload fields instead. See [custom-headers](custom-headers.md)
  for the full list and the field to use for each.
- **Payload size limit**: 30 MB total including headers, body, and
  attachments. Exceeding this raises `PayloadTooLargeError`.
- **Per-personalization recipients**: up to 1000 entries in `to`, `cc`, `bcc`
  each; up to 1000 personalizations per send; up to 1000 attachments.
- **Non-transactional sends** (those that generate `List-Unsubscribe`
  headers) **must** have exactly one recipient per personalization and be
  DKIM-signed. See [unsubscribe](unsubscribe.md).
- **`campaign_id`**: ≤ 48 UTF-8 characters and **no spaces**. `EmailParams`
  validates this at construction time. The value is echoed in every
  related webhook event.
- **Click tracking** only rewrites `<a>` tags whose URL is non-empty,
  starts with `http`/`https`, and does not have `clicktracking="off"`.
- **No server-side idempotency.** Retrying after a transient failure can
  produce duplicate sends. Build idempotency into the caller (e.g. a
  unique `campaign_id` + recipient-set check) when at-most-once delivery
  matters.

## Tracking

```python
mailchannels.Emails.queue(
    mailchannels.EmailParams(
        from_=mailchannels.EmailAddress(email="sender@example.com"),
        personalizations=[
            mailchannels.Personalization(
                to=[mailchannels.EmailAddress(email="recipient@example.net")],
            ),
        ],
        subject="Tracked",
        content=[
            mailchannels.Content(
                type="text/html",
                value="<p>Hello <a href='https://example.com'>click here</a></p>",
            ),
        ],
        tracking_settings=mailchannels.TrackingSettings(
            open_tracking=mailchannels.TrackingToggle(enable=True),
            click_tracking=mailchannels.TrackingToggle(enable=True),
        ),
    )
)
```

Open and click tracking require a subscription that supports them.

### Custom Tracking Domains

Pass `custom_domain_name` on a `TrackingToggle` (or on `unsubscribe_settings`)
to route those links through a domain you registered instead of the shared
MailChannels domain. The name must match an **active**
`CustomTrackingDomain` registered for that scope — see
[custom-tracking-domains](custom-tracking-domains.md) for registration and
DNS verification.

```python
mailchannels.EmailParams(
    from_=mailchannels.EmailAddress(email="sender@example.com"),
    personalizations=[
        mailchannels.Personalization(
            to=[mailchannels.EmailAddress(email="recipient@example.net")],
        ),
    ],
    subject="Tracked with a custom domain",
    content=[
        mailchannels.Content(
            type="text/html",
            value="<p>Hello <a href='https://example.com'>click here</a></p>",
        ),
    ],
    tracking_settings=mailchannels.TrackingSettings(
        click_tracking=mailchannels.TrackingToggle(
            enable=True,
            custom_domain_name="newsletter-clicks",
        ),
    ),
    unsubscribe_settings=mailchannels.UnsubscribeSettings(
        custom_domain_name="newsletter-unsubscribe",
    ),
)
```

## Reading The Response

Both methods return a `MailChannelsResponse` (a `dict` subclass with
attribute-style access; see [responses](responses.md)):

```python
resp = mailchannels.Emails.queue(message)

# `request_id` tracks the request across webhooks; same value via dict
# access or attribute access. Response headers (useful for support
# tickets) hang off `http_headers`.
```

For `Emails.send()` (non-dry-run), `resp.results` contains one `SendResult`
per personalization with `index`, `message_id`, `status` (`sent` / `failed`),
and a human `reason`. **`sent` is temporary** — the final delivery outcome
arrives via webhooks if you've enrolled.

For `Emails.queue()`, the response has `request_id` and `queued_at`. The
actual send outcome is delivered via webhooks.
