# Python SDK Overview

Start with the [official Python quickstart](https://docs.mailchannels.com/email-api/python/quickstart).
The repository's [framework recipes](../../../../docs/FRAMEWORKS.md) show direct
SDK use in Django and FastAPI. The Django recipe is a service function, not a
Django email backend or an Anymail provider. Use async SDK methods in async
application code and close the client when its application lifecycle ends.
For SDK development, follow the root `AGENTS.md`: run verification in Docker
on Linux or SmolVM on macOS, as documented in `docs/DEVELOPMENT.md`.

The Python `mailchannels` package (PyPI: `mailchannels`) exposes resources
both at module level and on an explicit `Client` instance. Pick the entry
point that fits the application's shape:

```python
import mailchannels

# Preferred: set MAILCHANNELS_API_KEY in the environment. The SDK reads it
# automatically — no Python-side configuration needed.
#   export MAILCHANNELS_API_KEY="..."
mailchannels.Emails.queue({...})                   # module-level resource

# Only when env vars aren't possible: assign module-level (still load the
# value from an env var or secret store, never hardcode it).
import os
mailchannels.api_key = os.environ["MAILCHANNELS_API_KEY"]

# Use an explicit Client when you need per-call credentials (e.g. per
# tenant) or other per-instance configuration.
client = mailchannels.Client(api_key=os.environ["MAILCHANNELS_EXAMPLE_SUBACCOUNT_API_KEY"])
client.emails.queue({...})
```

Module-level config is convenient for scripts and single-account services.
Use an explicit `Client` only when you need:

- Distinct API keys per tenant or sub-account in the same process.
- `strict_responses=True` typed Pydantic returns in type checkers.
- A custom HTTP transport (proxies, mTLS, telemetry, test fakes).

You almost never need to change the base URL — the default
(`https://api.mailchannels.net/tx/v1`) is what production traffic uses.
Only override it if MailChannels has given you a specific alternate
endpoint (e.g. a sandbox or regional URL); otherwise leave it alone.

## Key Concept: Personalizations

A single `Emails.send()` or `Emails.queue()` call can produce **many
individually-rendered messages**. Each entry in the `personalizations`
list is one rendered, addressed message: its own `to` / `cc` / `bcc`,
optional per-recipient template variables (`dynamic_template_data`),
optional per-recipient header overrides, and so on. The top-level
`from` / `subject` / `content` act as defaults that each personalization
can override.

A "personalization" is therefore not just "a recipient" — it is one
fully-resolved outgoing message. Several resources refer back to this
shape (templates, unsubscribe, custom headers, sub-account sends, etc.).

## Resource Inventory

| SDK surface | What it does |
| --- | --- |
| `Emails.send` / `Emails.send_async` | Send synchronously; full validation, supports dry-run. |
| `Emails.queue` / `Emails.queue_async` | Queue for fast handoff; per-recipient work runs in the background. |
| `CheckDomain.check` | DKIM / SPF / sender-domain / Domain Lockdown check. |
| `Dkim` | Create, list, update status, rotate hosted DKIM keys. |
| `SubAccounts` | Manage sub-accounts (multi-tenant). |
| `SubAccounts.ApiKeys` / `SubAccounts.SmtpPasswords` | Manage sub-account credentials. |
| `SubAccounts.Limits` | Set, get, delete per-sub-account send limits. |
| `Metrics` | Volume, engagement, performance, recipient-behaviour, sender metrics. |
| `Usage` | Parent-account usage for the current billing period. |
| `Suppressions` | List, create, delete suppression entries. |
| `Webhooks` | Enroll, validate, inspect batches, fetch public keys, verify signatures. |

## Path Variables

Pass raw identifiers to SDK methods. The SDK URL-encodes path variables such
as sub-account handles, DKIM domains/selectors, suppression recipients,
metric sender groups, and webhook batch IDs before building request URLs. Do
not pre-encode those values yourself; a literal `%` is encoded as `%25`.

## `send` vs `queue` And The Two Meanings Of "Async"

Four methods exist on `Emails`. The names are intentionally orthogonal:

| Method | Server behavior | Python execution |
| --- | --- | --- |
| `Emails.send()` | Regular send path; full per-recipient processing in the request. | sync (blocks the calling thread) |
| `Emails.send_async()` | Same as `send()`. | asyncio (`await`-able) |
| `Emails.queue()` | Queued send; per-recipient work runs in the background and the call returns faster. | sync (blocks the calling thread) |
| `Emails.queue_async()` | Same as `queue()`. | asyncio (`await`-able) |

`send` vs `queue` is a **server-side** distinction. `queue` returns faster
because per-recipient work is deferred. The `_async` suffix is a separate,
**client-side** distinction — Python asyncio. Default to `queue()` for most
production paths.

## Configuration Sources

**The recommended setup is to set `MAILCHANNELS_API_KEY` in the
environment and write no configuration code at all.** The SDK reads it
automatically the first time a request needs an API key, and your code
stays free of credentials.

When you do need to override that — multiple tenants in one process, a
test harness, etc. — the SDK looks for each setting in this priority
order:

1. Explicit `Client(api_key=..., http_client=...)`.
2. Module-level `mailchannels.api_key`, `mailchannels.default_http_client`,
   `mailchannels.default_async_http_client`, `mailchannels.strict_responses`.
3. Environment variables (`MAILCHANNELS_API_KEY`, and `MAILCHANNELS_API_URL`
   for the rarely-needed base-URL override).

The first non-empty value wins. The SDK sends the resolved key as the
`X-API-Key` header on every request.

The default base URL is `https://api.mailchannels.net/tx/v1` and almost
no application should change it. Only override `MAILCHANNELS_API_URL` (or
pass `base_url=` to `Client`) when MailChannels has given you a specific
alternate endpoint.

## Responses

Default returns are `MailChannelsResponse` instances — a `dict` subclass
that also supports attribute-style access, with HTTP headers preserved on
`.http_headers`. Strict mode (per-client or module-level) returns Pydantic
models for modeled endpoints and raises `ResponseValidationError` if the API
shape doesn't match the model. See [responses](responses.md).
