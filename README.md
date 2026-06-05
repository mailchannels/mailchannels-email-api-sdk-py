# MailChannels Python SDK

[![Build Status](https://img.shields.io/bitbucket/pipelines/mailchannels/mailchannels-email-api-sdk-py/main.svg)](https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/pipelines)
[![PyPI](https://img.shields.io/pypi/v/mailchannels)](https://pypi.org/project/mailchannels/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mailchannels)](https://pypi.org/project/mailchannels/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-46aef7.svg)](https://github.com/astral-sh/ruff)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/mailchannels)](https://pypi.org/project/mailchannels/)

<!-- generated:api-version -->
Built and tested against MailChannels Email API 0.21.1.
<!-- /generated:api-version -->

`mailchannels` is a typed Python SDK for the MailChannels Email API. It keeps
the first send small, then opens up the production features that matter when
email is part of a real product: queued delivery through `/send-async`,
MailChannels-hosted DKIM, domain validation, templates, unsubscribe behavior,
custom headers, metrics, suppressions, and webhooks.

MailChannels is especially strong for multi-tenant sending. Parent accounts can
create isolated sub-accounts, issue separate credentials, set granular limits,
inspect usage, and keep one customer's bad traffic from endangering the parent
account or other tenants.

The SDK accepts familiar dictionary payloads for quick scripts and Pydantic
models for codebases that prefer explicit runtime validation. Use the
module-level resources when you want Resend-style convenience; create explicit
`Client` instances when each tenant, account, or service needs its own
credentials.

## Start Here

- New to the SDK: start with [Five-Minute Quickstart](#five-minute-quickstart).
- Building a sending workflow: use [Common Sending Recipes](#common-sending-recipes).
- Building a multi-tenant product: read [Account And Domain Operations](#account-and-domain-operations).
- Operating at scale: jump to [Production Operations](#production-operations).
- Using an AI coding agent: see [Using This SDK With An AI Agent](#using-this-sdk-with-an-ai-agent).
- Looking for details: see [API Reference And Further Reading](#api-reference-and-further-reading).

## Five-Minute Quickstart

### Install

Install the SDK with uv:

```bash
uv add mailchannels
```

The synchronous client uses `requests`. Async HTTP support is optional:

```bash
uv add "mailchannels[async]"
```

### Configure

For small applications and scripts, set the module-level API key once and use
the top-level resources.

```python
import mailchannels

mailchannels.api_key = "YOUR-API-KEY"
```

The SDK also reads `MAILCHANNELS_API_KEY` and `MAILCHANNELS_API_URL` from the
environment. Environment variables are the cleanest option for deployed
services because the same code can run in development, staging, and production
without committing credentials or hostnames.

```bash
export MAILCHANNELS_API_KEY="YOUR-API-KEY"
```

For services that send on behalf of multiple accounts, create explicit clients.
Each client carries its own API key.

```python
import mailchannels

parent_client = mailchannels.Client(api_key="PARENT-ACCOUNT-API-KEY")
sub_account_client = mailchannels.Client(api_key="SUB-ACCOUNT-API-KEY")
```

### Send

Use `Emails.send()` when you want immediate validation feedback from the regular
send endpoint.

```python
import mailchannels

mailchannels.api_key = "YOUR-API-KEY"

email = mailchannels.Emails.send(
    {
        "from": {"email": "sender@example.com", "name": "Priya Patel"},
        "to": [{"email": "recipient@example.net", "name": "Sakura Tanaka"}],
        "subject": "Testing Email API",
        "text": "Hi Sakura. This is just a test from Priya.",
    }
)

print(email)
```

Use `Emails.queue()` for `/send-async` when your application should hand the
message to MailChannels quickly and continue without waiting for the regular
send path.

```python
queued = mailchannels.Emails.queue(
    {
        "from": {"email": "sender@example.com"},
        "to": [{"email": "recipient@example.net"}],
        "subject": "Queued message",
        "html": "<strong>Hello</strong>",
    }
)
```

This is usually the better default for high-throughput web applications, job
workers, or any path where email should not slow down the user-facing request.

### Send vs Queue, And The Two Meanings Of "Async"

The SDK exposes four sending methods, and the names can be confusing because
"async" means two different things:

| Method | API endpoint | Python execution |
| --- | --- | --- |
| `Emails.send()` | `/send` | synchronous (blocks the calling thread) |
| `Emails.send_async()` | `/send` | asyncio (`await`-able) |
| `Emails.queue()` | `/send-async` | synchronous (blocks the calling thread) |
| `Emails.queue_async()` | `/send-async` | asyncio (`await`-able) |

`send` vs `queue` is a **server-side** distinction: both endpoints run the
same request validation and have the same delivery semantics, but
`/send-async` defers some per-recipient processing into the background so the
request returns faster. The `_async` suffix is a separate, **client-side**
Python asyncio distinction — it's the same suffix used on every other resource
(e.g. `client.webhooks.list_async()`).

Rule of thumb: prefer `queue` when request latency matters, and especially
for sends with a large number of recipients — the per-recipient work on
the `/send` path can be slow enough that the request times out. Pick `send`
only when you specifically need the regular (non-deferred) path. Add `_async`
if you're calling from asyncio code.

## Core Concepts

### API Coverage

The SDK covers the MailChannels Email API surfaces that production senders need
most often:

| Need | SDK surface |
| --- | --- |
| Send now with `/send` | `mailchannels.Emails.send()` |
| Queue for processing with `/send-async` | `mailchannels.Emails.queue()` |
| Validate sender DNS and Domain Lockdown | `mailchannels.CheckDomain.check()` |
| Manage hosted DKIM keys | `mailchannels.Dkim` |
| Isolate tenants | `mailchannels.SubAccounts` |
| Cap tenant volume | `mailchannels.SubAccounts.Limits` |
| Inspect traffic health | `mailchannels.Metrics` |
| Manage suppressions | `mailchannels.Suppressions` |
| Receive delivery events | `mailchannels.Webhooks` |

Generated reports provide the deeper detail:

- [API coverage report](https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/main/docs/API_COVERAGE.md) summarizes endpoint coverage,
  contract-test coverage, online-test coverage, the OpenAPI spec hash, and the
  SDK version used for the report.
- [API reference](https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/main/docs/API_REFERENCE.md) lists public exports, classes, methods,
  parameters, return types, model fields, and compact examples from the SDK
  source.

### Choose An Entry Point

| Use this | When it fits |
| --- | --- |
| `mailchannels.Emails.send()` | You want synchronous validation from `/send`. |
| `mailchannels.Emails.queue()` | You want fast handoff to `/send-async`; this is usually best for web requests and workers. |
| `mailchannels.CheckDomain.check()` | You are onboarding or troubleshooting a sending domain. |
| `mailchannels.Dkim` | You need MailChannels to create, store, rotate, or validate hosted DKIM keys. |
| `mailchannels.SubAccounts` | You send for multiple tenants and need isolation, credentials, usage, or limits per tenant. |
| Explicit `mailchannels.Client(...)` | You need different API keys, base URLs, or HTTP transports in the same process. |

### Read Responses

SDK responses behave like ordinary dictionaries, but they also support
attribute access. HTTP response headers are preserved under `http_headers` for
diagnostics and request IDs.

```python
queued = mailchannels.Emails.queue(message)

print(queued["id"])
print(queued.id)
print(queued.http_headers)
```

Set `strict_responses=True` when you want modeled endpoints to return Pydantic
response objects instead. See [Advanced Usage](https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/main/docs/ADVANCED.md) for strict
response models, custom transports, API compatibility metadata, and client
lifecycle details.

### Use Typed Models

Dictionary payloads are convenient, but long-lived applications often benefit
from explicit types. `EmailParams`, `EmailAddress`, `Content`, and
`Personalization` are Pydantic models that validate the request before it reaches
the HTTP layer.

```python
params = mailchannels.EmailParams(
    from_=mailchannels.EmailAddress(email="sender@example.com"),
    personalizations=[
        mailchannels.Personalization(
            to=[mailchannels.EmailAddress(email="recipient@example.net")]
        )
    ],
    subject="Typed message",
    content=[
        mailchannels.Content(type="text/plain", value="Hello from typed models.")
    ],
)

mailchannels.Emails.send(params)
```

Use typed models when you are constructing messages across several functions or
want validation errors to appear close to the code that builds the payload.

## Common Sending Recipes

### Add Attachments

MailChannels expects attachment content to be Base64 encoded. The SDK's
`Attachment.from_bytes()` helper handles that encoding, infers a MIME type
from the filename, and preserves the MailChannels fields in the final send
payload. Read the file or fetch the URL yourself and pass the bytes in — the
SDK does not read files or make outbound HTTP requests on your behalf.

```python
from pathlib import Path

invoice = mailchannels.Attachment.from_bytes(
    Path("invoice.pdf").read_bytes(),
    filename="invoice.pdf",
)

mailchannels.Emails.queue(
    {
        "from": {"email": "billing@example.com"},
        "to": [{"email": "recipient@example.net"}],
        "subject": "Your invoice",
        "text": "Your invoice is attached.",
        "attachments": [invoice],
    }
)
```

### Preview With Dry Run

MailChannels supports dry-run validation on the send endpoint. Pass
`dry_run=True` to send the request for validation and rendering checks without
delivering the message.

```python
preview = mailchannels.Emails.send(
    {
        "from": {"email": "sender@example.com"},
        "to": [{"email": "recipient@example.net"}],
        "subject": "Dry run",
        "text": "Validate this message without delivering it.",
    },
    dry_run=True,
)
```

### Send A Template Email

MailChannels templates are part of the send payload rather than a separate
template CRUD API. Mark each templated content part with
`template_type: "mustache"` and provide recipient-specific values in
`dynamic_template_data`.

```python
preview = mailchannels.Emails.send(
    {
        "from": {"email": "sender@example.com"},
        "personalizations": [
            {
                "to": [{"email": "jane@example.net"}],
                "dynamic_template_data": {"name": "Jane Doe"},
            }
        ],
        "subject": "Template Example",
        "content": [
            {
                "type": "text/plain",
                "value": "Hello {{name}}",
                "template_type": "mustache",
            }
        ],
    },
    dry_run=True,
)
```

### Manage DKIM Keys

MailChannels can generate and store DKIM private keys for your account. Create a
key pair, publish the returned public DNS record in your own DNS zone, and then
reference the selector when sending.

```python
key = mailchannels.Dkim.create(
    "example.com",
    selector="mcdkim",
    algorithm="rsa",
    key_length=2048,
)

for record in key.get("dkim_dns_records", []):
    print(record["name"], record["type"], record["value"])
```

After the DNS record is published, send mail with the selector.

```python
mailchannels.Emails.queue(
    {
        "from": {"email": "sender@example.com"},
        "to": [{"email": "recipient@example.net"}],
        "subject": "DKIM signed message",
        "text": "This message is signed by a MailChannels-hosted DKIM key.",
        "dkim_domain": "example.com",
        "dkim_selector": "mcdkim",
    }
)
```

See [DKIM And DNS](https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/main/docs/DKIM.md) for key rotation, customer-managed private
keys, and a Cloudflare DNS publication example.

### Add Unsubscribe Support

MailChannels can render a hosted one-click unsubscribe URL inside mustache
content. Use the exported `UNSUBSCRIBE_URL_PLACEHOLDER` constant so the
placeholder is not mistyped. MailChannels requires exactly one recipient per
personalization when unsubscribe links are used.

```python
mailchannels.Emails.queue(
    {
        "from": {"email": "sender@example.com"},
        "personalizations": [{"to": [{"email": "recipient@example.net"}]}],
        "subject": "Newsletter",
        "content": [
            {
                "type": "text/html",
                "value": (
                    "<p>Hello</p>"
                    f"<a href='{mailchannels.UNSUBSCRIBE_URL_PLACEHOLDER}'>"
                    "unsubscribe</a>"
                ),
                "template_type": "mustache",
            }
        ],
    }
)
```

For automatic `List-Unsubscribe` headers, set `transactional` to `False`.
MailChannels documents that this mode also requires one recipient per
personalization and DKIM signing.

### Add Custom Email Headers

Use `headers` when a message needs additional application-specific metadata or
tracking values. MailChannels may reject restricted or duplicate headers, so
prefer a small, intentional set.

```python
mailchannels.Emails.send(
    {
        "from": {"email": "sender@example.com"},
        "to": [{"email": "recipient@example.net"}],
        "subject": "Custom Header Example",
        "text": "This email includes custom headers.",
        "headers": {
            "X-Campaign-ID": "newsletter-123",
        },
    }
)
```

Headers can also be set per personalization. If the same header exists globally
and on a personalization, MailChannels uses the personalization-level value.

### Async Python

Async methods use the same payloads as the synchronous methods and are named
with the `_async` suffix. Use them in FastAPI, Starlette, aiohttp workers, or
other asyncio applications where blocking the event loop would be the wrong
tradeoff.

```python
import asyncio
import mailchannels

mailchannels.api_key = "YOUR-API-KEY"


async def main() -> None:
    queued = await mailchannels.Emails.queue_async(
        {
            "from": {"email": "sender@example.com"},
            "to": [{"email": "recipient@example.net"}],
            "subject": "Queued message",
            "text": "Hello",
        }
    )
    print(queued)


asyncio.run(main())
```

Install `mailchannels[async]` before using async methods.

## Account And Domain Operations

### Sub-Accounts

Sub-accounts are a major MailChannels feature, so they are exposed as a
top-level resource. Parent accounts can create sub-accounts, issue API keys,
manage SMTP passwords, set limits, and inspect usage.

```python
sub_account = mailchannels.SubAccounts.create(
    company_name="Client A",
    handle="clienta",
)

sub_accounts = mailchannels.SubAccounts.list(limit=100, offset=0)
api_key = mailchannels.SubAccounts.ApiKeys.create("clienta")
```

Rate limits are useful when each customer, tenant, or downstream sender should
have its own monthly allocation.

```python
limit = mailchannels.SubAccounts.Limits.set(
    "clienta",
    sends=100_000,
)

current_limit = mailchannels.SubAccounts.Limits.retrieve("clienta")
```

Usage stats let you show customers how much of their allocation has been used
or decide when to raise, lower, or suspend a limit.

```python
usage = mailchannels.SubAccounts.retrieve_usage("clienta")
parent_usage = mailchannels.Usage.retrieve()
```

When sending as a sub-account, create a separate client with that sub-account's
API key. This keeps account boundaries explicit in code.

```python
client = mailchannels.Client(api_key="SUB-ACCOUNT-API-KEY")
client.emails.queue(
    {
        "from": {"email": "sender@client.example"},
        "to": [{"email": "recipient@example.net"}],
        "subject": "Client message",
        "text": "Hello",
    }
)
```

### Domain Checks

Before sending from a domain, ask MailChannels to verify the domain's
authentication posture. `CheckDomain.check()` calls `/check-domain` and returns
the API's DKIM, SPF, sender-domain DNS, and Domain Lockdown results.

```python
result = mailchannels.CheckDomain.check("example.com")

print(result.check_results["spf"]["verdict"])
print(result.references)
```

If you use MailChannels-hosted DKIM keys, pass the selector you expect the
domain to use.

```python
result = mailchannels.CheckDomain.check(
    "example.com",
    dkim_settings=[
        mailchannels.DkimSetting(
            dkim_domain="example.com",
            dkim_selector="mcdkim",
        )
    ],
)
```

## Production Operations

### Metrics

Metrics endpoints expose the operational view of your email traffic. Use them
to build dashboards, reconcile campaign performance, or monitor sender health.

```python
engagement = mailchannels.Metrics.engagement(
    start_time="2026-04-01",
    end_time="2026-04-24T00:00:00Z",
    campaign_id="newsletter",
    interval="day",
)
```

Sender metrics group results by campaigns or sub-accounts and support ordinary
pagination controls.

```python
senders = mailchannels.Metrics.senders(
    "sub-accounts",
    limit=50,
    offset=0,
    sort_order="desc",
)
```

Available metrics methods are `engagement()`, `performance()`,
`recipient_behaviour()`, `volume()`, and `senders()`. The British spelling
matches the underlying `/metrics/recipient-behaviour` endpoint.

### Suppression Lists

Suppression lists are the MailChannels-native way to keep known unwanted
recipients out of future sends. The SDK exposes list, create, and delete
operations.

```python
mailchannels.Suppressions.create(
    [
        {
            "recipient": "recipient@example.net",
            "suppression_types": ["non-transactional"],
            "notes": "Imported from billing system preference center.",
        }
    ],
    add_to_sub_accounts=True,
)

entries = mailchannels.Suppressions.list(
    source="api",
    limit=100,
)

mailchannels.Suppressions.delete("recipient@example.net", source="all")
```

`add_to_sub_accounts=True` is useful for parent-account workflows where one
suppression should be copied across the tenant accounts beneath it.

### Webhooks

MailChannels can send delivery events to your application for accepted,
delivered, bounced, opened, clicked, complained, and unsubscribed messages. The
SDK exposes webhook enrollment, validation, batch inspection, batch resend, and
public signing-key retrieval.

```python
mailchannels.Webhooks.create("https://example.com/mailchannels/events")

validation = mailchannels.Webhooks.validate(request_id="test_request_1")
batches = mailchannels.Webhooks.batches(statuses=["4xx", "5xx"], limit=50)

mailchannels.Webhooks.resend_batch(12345)
```

Webhook receivers should verify the `customer_handle` in each event and check
the signature headers MailChannels sends with the request. The SDK can verify
the `Content-Digest`, replay age, and RFC 9421 Ed25519 signature when given the
public signing key returned by `Webhooks.public_key(...)`.

```python
import mailchannels
from mailchannels import (
    signature_key_id,
)


def receive_webhook(headers: dict[str, str], body: bytes) -> None:
    """Verify a webhook before processing events."""
    key_id = signature_key_id(headers)
    if key_id is None:
        raise ValueError("Missing MailChannels webhook key ID")

    public_key = mailchannels.Webhooks.public_key(key_id)

    if not mailchannels.Webhooks.verify(headers, body, public_key):
        raise ValueError("Invalid MailChannels webhook signature")
```

### Error Handling

The SDK maps common MailChannels API failures to typed exceptions. Catch the
specific error when your application can respond differently to authentication,
authorization, invalid requests, missing resources, rate limits, conflicts,
payload size problems, or server-side failures.

```python
try:
    mailchannels.Emails.queue(message)
except mailchannels.PayloadTooLargeError:
    raise
except mailchannels.ForbiddenError:
    raise
except mailchannels.RateLimitError:
    raise
except mailchannels.NotFoundError:
    raise
except mailchannels.InvalidRequestError:
    raise
except mailchannels.ServerError:
    raise
```

Each exception carries structured metadata for logs and support workflows:
`status_code`, `code`, `error_type`, `headers`, `request_id`, `retry_after`,
`suggested_action`, and the parsed API `response`. Use `to_dict()` when you want
to send consistent error metadata to your logger.

## API Reference And Further Reading

- [API reference](https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/main/docs/API_REFERENCE.md) is the generated public surface
  reference.
- [API coverage](https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/main/docs/API_COVERAGE.md) shows endpoint, contract-test, and online
  test coverage against the MailChannels OpenAPI document.
- [Advanced usage](https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/main/docs/ADVANCED.md) covers strict responses, custom transports,
  API compatibility metadata, client lifecycle, and low-level webhook helpers.
- [DKIM and DNS](https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/main/docs/DKIM.md) covers hosted DKIM keys, rotation, customer-managed
  keys, and Cloudflare DNS publication.
- [Development](https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/main/docs/DEVELOPMENT.md) covers local checks, online tests, SmolVM,
  CI, and publishing.
- `examples/` contains tested examples for async sending, attachments,
  templates, unsubscribe, custom headers, DKIM, Cloudflare DKIM publication,
  sub-accounts, metrics, domain checks, suppressions, webhooks, usage, custom
  HTTP clients, and structured error handling.

## Using This SDK With An AI Agent

This repository ships a complete agent skill at
[`.agents/skills/mailchannels-python/`](https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/main/.agents/skills/mailchannels-python/).
It teaches an AI coding agent how to use the `mailchannels` package
correctly — the same recipes documented in this README, broken into
focused per-topic files and prefixed with a decision tree so the agent
loads only the parts the task actually needs.

Layout:

```
.agents/skills/mailchannels-python/
├── SKILL.md              # entry point: scope, decision tree, conventions
└── resources/            # focused recipes (sending, dkim, webhooks, …)
```

Every file is plain Markdown. The skill works with any agent that can be
pointed at a directory of context files — Claude Code, Cursor, Codex CLI,
Aider, Continue, and similar tools all consume it without modification.

### Install

The skill ships inside the `mailchannels` PyPI source distribution. Use
`pip download` to fetch the sdist, extract it, and copy the skill
directory wherever your agent looks for skills, rules, or context files:

```bash
# Pin the version to match the SDK you have installed — omit the pin to
# grab the latest release:
pip download --no-deps --no-binary :all: --dest /tmp/mc-python-sdk mailchannels

tar -xzf /tmp/mc-python-sdk/mailchannels-*.tar.gz -C /tmp/mc-python-sdk

# Get the name of the extracted directory, which includes the version number: (e.g. `mailchannels-1.0.0`):
sdk_dir=$(ls /tmp/mc-python-sdk/ -I *.tar.gz)

# Replace the destination with your agent's path:
mkdir -p <your-agent's-skills-dir>
cp -r /tmp/mc-python-sdk/${sdk_dir}/.agents/skills/mailchannels-python <your-agent's-skills-dir>/

rm -rf /tmp/mc-python-sdk
```

`--no-binary :all:` forces pip to download the source distribution
(`.tar.gz`) rather than the wheel; the wheel only contains the importable
Python package and doesn't carry the agent skill. `--no-deps` skips
dependency downloads since you only need the SDK's own sdist.

Re-run the same commands when you upgrade the SDK so the skill stays in
step with the installed version.

Common destinations:

| Agent | Where to put it |
| --- | --- |
| Claude Code | `.claude/skills/` (project) or `~/.claude/skills/` (user) |
| Cursor | `.cursor/rules/` (or attach files inline with `@`) |
| Codex CLI | referenced from the project's `AGENTS.md` |
| Aider | referenced from the conventions file in `.aider.conf.yml` |
| Continue | registered as a custom context provider |

If your tool isn't listed, look for the equivalent of "skill", "rule",
"context bundle", or "conventions file" — any mechanism that lets the
agent read a directory of Markdown will work.

### Workflow

The flow is the same regardless of agent:

1. The agent loads `SKILL.md` for the scope statement and decision tree.
2. The decision tree routes to the relevant `resources/*.md` file(s).
3. The agent reads only those files; no need to preload everything.

Ask the agent to "send an email with MailChannels", "verify a webhook
signature", "rotate a DKIM key", or any similar task in the SDK's
domain. The skill's frontmatter `description` tells the agent when to
engage, and the body tells it what to do.

## License

MIT License. See [LICENSE](https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/main/LICENSE).
