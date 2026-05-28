# Error Handling

All SDK exceptions inherit from `MailChannelsError`. API response errors
inherit from `ApiError` (which inherits from `MailChannelsError`). Catch the
specific exception when behavior should differ; only fall back to the bases
for top-level logging.

## Exception Hierarchy

```
MailChannelsError
├── ConfigurationError              missing API key, etc.
├── AsyncClientNotConfigured        called *_async without [async] extra
├── ResponseValidationError         strict_responses=True saw an off-shape API response
└── ApiError                        any non-2xx from the API
    ├── AuthenticationError         401 — invalid / missing API key
    ├── ForbiddenError              403 — feature not enabled, sub-account limits
    ├── InvalidRequestError         400 — bad payload, validation errors
    ├── ConflictError               409 — duplicate webhook, duplicate suppression, etc.
    ├── PayloadTooLargeError        413 — over the 30 MB limit
    ├── RateLimitError              429 — slow down; check retry_after
    ├── BadGatewayError             502 — upstream MTA unhappy
    └── ServerError                 5xx — generic server-side failure
```

## Catching Patterns

```python
import mailchannels

try:
    mailchannels.Emails.queue(message)
except mailchannels.PayloadTooLargeError:
    # Split the recipient list and retry, or shrink attachments.
    raise
except mailchannels.RateLimitError as exc:
    sleep_for = exc.retry_after or 10
    # back off and retry
    raise
except mailchannels.InvalidRequestError as exc:
    # Application bug — fix the payload, don't retry blindly.
    logger.error("Invalid request: %s", exc.to_dict())
    raise
except mailchannels.AuthenticationError:
    # Wrong API key. Don't retry.
    raise
except mailchannels.ForbiddenError:
    # Feature gated or sub-account suspended. Don't retry.
    raise
except mailchannels.ServerError:
    # Transient. Retry with backoff.
    raise
```

The order above matters: catch specific subclasses **before** broader ones.

## Useful Attributes On `ApiError`

Every `ApiError` exposes:

| Attribute | Meaning |
| --- | --- |
| `status_code` | HTTP status as `int` (or `None` for transport errors). |
| `code` | Stable error code string, e.g. `AttachmentReadError`, `InvalidPayload`. |
| `error_type` | Coarse classification, e.g. `validation`, `authorization`. |
| `headers` | Response headers dict (lower-cased keys). |
| `request_id` | Server-assigned ID — include in support tickets. |
| `retry_after` | Seconds to wait, parsed from `Retry-After`. |
| `suggested_action` | Server-suggested next step, if any. |
| `response` | Parsed API body. |
| `to_dict()` | Structured dict suitable for logging. |

```python
except mailchannels.ApiError as exc:
    logger.error("MailChannels error", extra=exc.to_dict())
```

## Client-Side Validation Errors

These raise `InvalidRequestError` before any HTTP call:

- Missing sender / recipient / subject / content.
- Empty `to`/`personalizations`/`content` collections.
- Invalid email-address shape.
- Reserved headers in `headers`.
- Wrong types in `headers` values (non-strings).

Failing early gives the caller a precise error rather than a vague 400.

## Attachment-Specific Errors

Constructing attachments can fail with `MailChannelsError` and:

- `code="AttachmentReadError"` — local file not found / unreadable.
- `code="AttachmentFetchError"` — `Attachment.from_url()` couldn't fetch.

These are not API errors — they originate inside the helper and won't have
`status_code`.

## Retrying And Idempotency

| Exception | Safe to retry? |
| --- | --- |
| `InvalidRequestError`, `AuthenticationError`, `ForbiddenError`, `ConflictError`, `PayloadTooLargeError` | **No** — these are caller problems; fix the input or credentials instead. |
| `RateLimitError` | Yes, after `exc.retry_after` seconds. |
| `ServerError`, `BadGatewayError` | Yes, with exponential backoff. |

The SDK does **not** retry automatically — each call site decides its
policy. The API also does not offer idempotency keys, so retrying
`Emails.send()` / `Emails.queue()` after a transient failure can produce a
duplicate send. Build idempotency into the caller (e.g. a unique
`campaign_id` + recipient-set check) when at-most-once delivery matters.
`Webhooks.resend_batch()` is always safe to call again — each call is a
separate resend attempt.

## Strict Response Errors

If `strict_responses=True` is set and the API returns a payload that doesn't
match the expected Pydantic model, the SDK raises `ResponseValidationError`
**before** returning. The original response is on the exception. Use the
default (loose) mode if upstream schema drift would otherwise crash your
service. See [responses](responses.md).

## Never Catch Bare `Exception`

If a particular failure can't be handled meaningfully, let it propagate.
Catching the bare `Exception` (or even `MailChannelsError`) silently swallows
bugs.
