# Reading Responses

By default the SDK returns `MailChannelsResponse` instances. They are a
`dict` subclass that also supports attribute-style access via
`__getattr__`, and preserve the HTTP headers under `http_headers`.

**Prefer attribute access** for response fields — it reads consistently
across loose and strict modes and stays valid when a future SDK release
promotes an endpoint to a typed Pydantic response. Snippets and
application code in this skill use attribute access throughout.

```python
# Default loose mode (or pass strict_responses=False explicitly) returns
# MailChannelsResponse — a dict subclass with attribute-style access.
client = mailchannels.Client(api_key="...", strict_responses=False)
resp = client.emails.queue(message)

resp.request_id         # canonical: attribute access
resp.http_headers       # response headers (always populated)
```

Because `MailChannelsResponse` is also a `dict` subclass, `resp["request_id"]`
works at runtime in loose mode — convenient for JSON-serialization paths
(`dict(resp)`), `**resp` unpacking, and the like — but use it sparingly:
strict-mode responses are Pydantic models that aren't indexable.

For non-2xx responses the SDK raises an `ApiError` subclass and the
HTTP status is on `exc.status_code` — see
[error-handling](error-handling.md).

## Strict Responses (Pydantic Models)

When `strict_responses=True` is set, **modeled** endpoints return Pydantic
model instances instead of `MailChannelsResponse`. The SDK raises
`ResponseValidationError` if the API payload doesn't fit the model.

```python
# Per client — recommended; type checkers see precise return types.
strict_client = mailchannels.Client(api_key="...", strict_responses=True)
strict_resp = strict_client.emails.queue(message)   # QueuedSendResponse

# Module-level — works at runtime, but module-level return types stay broad
# in type checkers because the flag is mutable at runtime.
mailchannels.strict_responses = True
```

### What's modeled

| Resource | Response model(s) |
| --- | --- |
| `Emails.send` (regular) | `SendResponse` — has `request_id` and per-personalization `results`. |
| `Emails.send` (dry run) | `SendResponse` — has `data` (list of rendered messages). |
| `Emails.queue` | `QueuedSendResponse` — has `request_id` and `queued_at`. |
| `CheckDomain.check` | `CheckDomainResult` |
| `Usage.retrieve` | `UsageStats` |

Endpoints that aren't modeled keep returning loose `MailChannelsResponse`
even under strict mode.

## Choosing Strict vs Loose

| Use loose (default) when… | Use strict when… |
| --- | --- |
| Calling code is dict-shaped and tolerant. | You want type checker autocomplete on response fields. |
| You explicitly want forward-compat with future API fields. | You want to catch breaking-change response drift fast. |
| You serialize the response to JSON / a queue anyway. | You map fields into your own typed domain models. |

## Empty Bodies

Endpoints that return `204 No Content` (suspend / activate / delete /
limit delete) yield an `EmptyResponse` Pydantic model that still carries
`http_headers`. Its truthiness is `False`, so `if resp:` works as a
"did the call return content?" check.
