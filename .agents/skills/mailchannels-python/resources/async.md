# Async (asyncio) Usage

Every resource method has an `_async` variant with the same signature and
return semantics, except the variant is `await`-able.

```python
import asyncio
import mailchannels

mailchannels.api_key = "YOUR-API-KEY"


async def main() -> None:
    resp = await mailchannels.Emails.queue_async(
        mailchannels.EmailParams(
            from_=mailchannels.EmailAddress(email="sender@example.com"),
            personalizations=[
                mailchannels.Personalization(
                    to=[mailchannels.EmailAddress(email="recipient@example.net")],
                ),
            ],
            subject="Hello",
            content=[mailchannels.Content(type="text/plain", value="Hi")],
        )
    )
    print(resp.request_id)


asyncio.run(main())
```

## Install The Async Extra

The default install only carries `requests`. For async transport you need
`httpx`:

```bash
uv add "mailchannels[async]"
# or:
uv pip install "mailchannels[async]"
```

Forgetting this raises `AsyncClientNotConfigured` the first time you call any
`_async` method.

## Don't Mix Sync And Async In An Event Loop

`Emails.send()` (no `_async`) blocks the calling thread, even in asyncio
code. From inside `async def`, always use the `_async` variant so the event
loop stays responsive.

```python
# WRONG — blocks the event loop
await some_coroutine()
mailchannels.Emails.queue(message)

# RIGHT
await mailchannels.Emails.queue_async(message)
```

## Async Client Lifecycle

The module-level async transport (`HTTPXClient`) is lazily created the first
time any `_async` method runs. For deterministic shutdown — especially in
FastAPI / Starlette `lifespan` handlers — close it explicitly:

```python
if mailchannels.default_async_http_client is not None:
    await mailchannels.default_async_http_client.aclose()
```

If you use explicit clients, `async with` is the idiomatic form:

```python
async with mailchannels.Client(api_key="...") as client:
    await client.emails.queue_async(message)
```

## Concurrent Sends

The httpx transport reuses a single pooled `AsyncClient`. Firing many
`_async` calls concurrently with `asyncio.gather()` is supported and the
intended way to scale parallel sends.

```python
async def fan_out(messages: list[mailchannels.EmailParams]) -> None:
    await asyncio.gather(*(mailchannels.Emails.queue_async(m) for m in messages))
```

## Naming Reminder

The `_async` suffix means **Python asyncio**, not MailChannels' queued
send path. `send` vs `queue` is the server-side distinction; `_async` is
the client-side distinction. The full four-method table is in
[overview](overview.md); the send-vs-queue tradeoff is in
[sending](sending.md).
