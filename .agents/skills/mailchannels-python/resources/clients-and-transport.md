# Setting Up The MailChannels Python Client

Before any call works the Python SDK (`mailchannels` on PyPI) needs to
know **which API key to send**, and optionally where to send it and which
HTTP transport to use. This document is the one-stop reference for that
setup. Other-language MailChannels SDKs configure clients differently —
none of the snippets here transfer.

## TL;DR

```python
import mailchannels

# Set MAILCHANNELS_API_KEY in the environment; the SDK reads it
# automatically and no Python-side configuration is needed.
#   export MAILCHANNELS_API_KEY="YOUR-API-KEY"
mailchannels.Emails.queue({...})
```

That covers single-account use. The rest of this document covers the
choices you have when the simple path doesn't fit: per-tenant `Client`
instances, custom HTTP transports, lifecycle, and the (rare) base-URL
override.

## API Keys

### Precedence Order

When the SDK needs an API key it walks this chain and uses the first
non-empty value it finds:

1. The `api_key=` argument passed to `mailchannels.Client(...)`.
2. `mailchannels.api_key` (module-level attribute).
3. The `MAILCHANNELS_API_KEY` environment variable.

If nothing in the chain is set, calls raise `ConfigurationError`. The
resolved key is sent as the `X-API-Key` header on every request.

Empty strings fall through — `Client(api_key="")` and
`mailchannels.api_key = ""` both behave the same as `None` and let the
next layer take over. To explicitly clear a module-level value in tests,
set it to `None`.

### Where To Get Them

Parent-account keys are created in the MailChannels dashboard.
Sub-account keys are created programmatically from the parent account:

```python
parent = mailchannels.Client(api_key="PARENT-ACCOUNT-API-KEY")
sub_key = parent.sub_accounts.api_keys.create("tenant_handle")
# Full value returned ONCE — persist it to your secret store immediately.
```

See [sub-accounts](sub-accounts.md) for the full sub-account workflow.

### Multi-Tenant: One Client Per Credential

Never mix a parent key and a sub-account key on the same module-level
configuration — bugs caused by "wrong key, wrong call site" are hard to
spot. Give each tenant its own `Client`:

```python
parent = mailchannels.Client(api_key="PARENT-ACCOUNT-API-KEY")
tenant_a = mailchannels.Client(api_key="TENANT-A-API-KEY")
tenant_b = mailchannels.Client(api_key="TENANT-B-API-KEY")

parent.sub_accounts.list(limit=100)
tenant_a.emails.queue({...})
tenant_b.emails.queue({...})
```

Each `Client` carries its own key and never falls back to the
module-level or env-var key.

## Module-Level vs Explicit Client

Pick the entry point that fits your application shape:

| Use… | When |
| --- | --- |
| Module-level config | Scripts, one-shot CLIs, single-account services. Fastest setup. |
| Explicit `Client` | Multi-tenant code, multiple credentials, a custom HTTP transport, or strict Pydantic return types in your type checker. |

```python
# Module-level
mailchannels.api_key = "YOUR-API-KEY"
mailchannels.strict_responses = False    # default

# Explicit
client = mailchannels.Client(
  api_key="YOUR-API-KEY",
  strict_responses=True,               # see resources/responses.md
  # http_client= and async_http_client= are optional —
  # see "Custom HTTP Transports".
)
```

## Base URL (Rarely Needed)

The default base URL is `https://api.mailchannels.net/tx/v1`. Almost no
application should override it — only do so if MailChannels has given
you a specific alternate endpoint (sandbox or regional URL).

If you do need to override, the same three-layer precedence applies as
for the API key:

1. `Client(base_url="https://…")`.
2. `mailchannels.base_url = "https://…"`.
3. `MAILCHANNELS_API_URL` environment variable.

## Client Lifecycle

The default transports pool connections, so keep a single `Client` (or
keep using the module-level singleton) for the life of the process.

| Need | Do |
| --- | --- |
| Shut down explicitly | `client.close()` (sync) or `await client.aclose()` (async). |
| Scope to a block | Use it as a context manager. |
| Short-lived script | Don't worry about it — the GC closes on exit. |

```python
with mailchannels.Client(api_key="...") as c:
    c.emails.queue({...})

async with mailchannels.Client(api_key="...") as c:
    await c.emails.queue_async({...})
```

For module-level config, the pooled transports are exposed at
`mailchannels.default_http_client` and
`mailchannels.default_async_http_client` in case you need to call
`.close()` / `.aclose()` on them during a graceful shutdown.

A few related gotchas:

- Closing one `Client` doesn't close the module-level transports, and
  vice versa. Each instance owns its own pool.
- Async calls without `mailchannels[async]` installed raise
  `AsyncClientNotConfigured`. Install the extra or supply your own
  `async_http_client=`.

## Custom HTTP Transports

The SDK accepts any object that satisfies its transport protocol. Useful
when you need outbound proxies, mTLS, custom retries / circuit breakers,
telemetry, or canned responses for tests.

### The Protocols

```python
from typing import Any
from mailchannels import SyncHTTPClient, AsyncHTTPClient, SDKResponse


class MySyncTransport:
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> SDKResponse:
        # Issue the request through your underlying client and return an
        # SDKResponse holding the parsed body, status code, and headers.
        raise NotImplementedError


class MyAsyncTransport:
    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> SDKResponse:
        raise NotImplementedError
```

The protocols are structural (`typing.Protocol`) — you don't need to
inherit from them; just match the `request` signature.

`SDKResponse` is what every transport must return. Construct one from
your underlying response (it preserves `status_code`, parsed `data`,
raw `text`, and headers).

### Plugging It In

```python
# Per-client (preferred — explicit and scoped)
custom_client = mailchannels.Client(
    api_key="...",
    http_client=MySyncTransport(),
    async_http_client=MyAsyncTransport(),
)

# Module-level (the defaults are typed narrowly; cast or `# type: ignore`
# if your static checker complains about the assignment).
mailchannels.default_http_client = MySyncTransport()   # type: ignore[assignment]
mailchannels.default_async_http_client = MyAsyncTransport()   # type: ignore[assignment]
```

### Common Patterns

- **Outbound proxy / mTLS** — wrap a pre-configured `requests.Session`
  or `httpx.AsyncClient` inside a thin transport. Re-use a single
  underlying client across all requests so connections pool.
- **Telemetry** — subclass `RequestsClient` / `HTTPXClient` (the SDK's
  defaults) and emit a span or metric around `super().request(...)`.
- **Tests** — return canned `SDKResponse` values for offline tests. For
  httpx specifically, `respx` is also a clean option without writing a
  full transport.

The default transports send `User-Agent: mailchannels-python/{version}`.
If your custom transport replaces them entirely, keep that header (or
something similar) so MailChannels support can correlate traffic.

## Version Metadata

```python
mailchannels.__version__          # "1.3.0"
mailchannels.get_version()        # same

mailchannels.API_SPEC_COMPATIBILITY.to_dict()
# {
#   "source_url": "...",
#   "openapi_version": "1.5.0",
#   "sha256": "...",
#   "checked_at": "...",
#   "sdk_version": "1.3.0",
# }
```

`API_SPEC_COMPATIBILITY` is the immutable record of which MailChannels
API spec the installed SDK release was built and tested against. Log it
on service startup if you want a paper trail.

### Redirects

The built-in synchronous and asynchronous transports do not follow HTTP
redirects, including redirects to the same host. This prevents forwarding
`X-Api-Key` and replaying send or management requests at a redirect target.
A redirect raises `ApiError` through `Client`, with the original status and
response headers. Direct transport calls return the original `SDKResponse`.
Configure the intended API base URL explicitly; do not automatically retry a
redirect or copy its `Location` into a new request. Custom transports should
also disable redirect following. Response bodies are still read normally;
this policy does not impose a response-size limit or a total elapsed deadline.
