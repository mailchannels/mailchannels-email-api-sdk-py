# Webhooks

MailChannels posts batched delivery events to a URL you register. Events
cover both `Emails.send()` and `Emails.queue()` sends and use the same
payload shape.

Throughout this document, "customer handle" is the unique string that
identifies your MailChannels account (or sub-account); the SDK derives it
from the API key and includes it on every event payload so multi-tenant
receivers can route correctly.

## Enroll And Manage

```python
import mailchannels

mailchannels.Webhooks.create("https://example.com/mailchannels/events")
mailchannels.Webhooks.list()           # list of enrolled URLs
mailchannels.Webhooks.delete_all()     # removes ALL enrolled webhooks
```

There is no per-URL delete — `delete_all()` removes every enrolled webhook
for the customer. Enroll the replacement first if you're swapping URLs.

If the endpoint is already enrolled, `create()` raises `ConflictError`.

The endpoint URL can be up to 8000 characters.

## Validate

`Webhooks.validate()` sends a synthetic test request to **every** enrolled
webhook and reports each one's response. Useful as a deploy check.

```python
result = mailchannels.Webhooks.validate(request_id="deploy-smoke-test")

if result.all_passed:
    print("All webhooks responded with 2xx")
for entry in result.results:
    print(entry.webhook, entry.result, entry.response)
```

Provide a `request_id` (max 28 chars) so the test event is easy to spot in
logs. If you don't pass one, MailChannels generates it. The test payload
carries `event: "test"` and a hardcoded sender of `test@mailchannels.com`.

## Inspect Batches

`Webhooks.batches()` returns up to 500 batch summaries with status, status
code, duration, and event count. Use it to investigate failed deliveries.

```python
batches = mailchannels.Webhooks.batches(
    statuses=["4xx", "5xx", "no_response"],   # any of 1xx | 2xx | 3xx | 4xx | 5xx | no_response
    created_after="2026-05-20",
    created_before="2026-05-25",              # range cannot exceed 31 days
    webhook="https://example.com/mailchannels/events",
    limit=500,                                # 1..500, default 500
    offset=0,
)
```

If neither `created_after` nor `created_before` is set, the default range is
the last 3 days.

## Resend A Batch

```python
result = mailchannels.Webhooks.resend_batch(12345)

print(result.status_code, result.duration_in_ms)
```

The response describes the resend attempt — a successful call here means
the attempt completed, **not** that your webhook responded with 2xx.
Inspect `status_code` (HTTP code your endpoint returned) and
`duration_in_ms` on the response to check what your endpoint actually
did.

## Verify Incoming Webhooks (Crucial)

MailChannels signs every webhook request with an Ed25519 signature.
`Webhooks.verify()` does the full verification — content digest, freshness,
and signature — in one call. Always verify before processing.

```python
import mailchannels


def receive(headers: dict[str, str], raw_body: bytes) -> None:
    key_id = mailchannels.signature_key_id(headers)
    if key_id is None:
        raise ValueError("Missing MailChannels webhook key ID")

    public_key = mailchannels.Webhooks.public_key(key_id)
    if not mailchannels.Webhooks.verify(headers, raw_body, public_key):
        raise ValueError("Invalid MailChannels webhook signature")

    # Safe to process from here.
```

`Webhooks.verify()` checks all three things in one call:

1. **Content-Digest** — SHA-256 of the raw body matches the header.
2. **Freshness** — `created` timestamp is within the default replay window
   (300 s old, 30 s future skew).
3. **Signature** — Ed25519 verifies against the public key for the given
   `key_id`.

**`raw_body` must be the unmodified request bytes.** If your framework
deserializes JSON, fetch the original bytes (e.g. `request.body` in Django,
`await request.body()` in FastAPI/Starlette) — not the parsed dict.

For low-level diagnostics, the helpers each step uses are also exposed:
`verify_content_digest(headers, body)`,
`parse_signature_input(value)`, and
`signature_is_fresh(parameters, max_age_seconds=300, max_skew_seconds=30)`.

Cache `Webhooks.public_key(key_id)` — the key only changes on rotation,
and MailChannels may publish multiple active keys at once during a
rollover. Always fetch by the `key_id` from the incoming request rather
than holding a single "current" key.

## Event Payloads

Each request body is a JSON **array** of event objects with shared fields:

```json
{
  "event": "delivered",
  "customer_handle": "your_customer_handle",
  "timestamp": 1716628800,
  "request_id": "req_abc...",
  "smtp_id": "MID-xxx",
  "email": "recipient@example.net",
  "recipients": ["recipient@example.net"],
  "status": "delivered",
  "reason": "250 OK"
}
```

Event values are one of:

`open`, `click`, `processed`, `delivered`, `dropped`, `hard-bounced`,
`soft-bounced`, `unsubscribed`, `complained`, `test`.

The SDK exposes a typed `WebhookEventPayload` model if you want validation:

```python
from mailchannels import WebhookEventPayload

events = [WebhookEventPayload.model_validate(item) for item in payload]
```

The model uses `extra="allow"` so additional fields are preserved.

## Responding

Return any 2xx status code quickly. MailChannels treats anything else as a
failure and may retry. Keep your handler thin: enqueue the event and return,
do the actual processing on a worker.
