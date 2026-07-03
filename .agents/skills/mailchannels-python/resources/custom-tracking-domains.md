# Custom Tracking Domains

Register your own hostname for click tracking, open tracking, or unsubscribe
links instead of MailChannels' shared domains. Once a domain is `active`,
select it by `name` via `custom_domain_name` on the send payload — see
[sending.md](sending.md#custom-tracking-domains).

## Register A Domain

```python
import mailchannels

domain = mailchannels.CustomTrackingDomains.create(
    name="newsletter-clicks",     # label used at send time, ^[a-z0-9-]+$, max 64
    hostname="click.example.com",
    scope="click",                # click | open | unsubscribe
)
```

Before this can complete, `hostname` needs a CNAME record pointing to
`links.mailchannels.net`.

## DNS Verification Is A Two-Step, Non-Error Flow

`create()` and `update()` (when re-activating a disabled domain) return one
of two shapes in the same `CustomTrackingDomainResult` — both are 2xx
responses, not errors:

- **Registered**: `name`, `hostname`, `scope`, `status`, `created_at` are
  all present.
- **Pending**: at least one of `instructions`, `token`, `txt_record_name`,
  `txt_record_value` is present (a CNAME-only failure can omit the TXT
  fields; a fresh registration includes all of them).

Use a strict client here — the two shapes share no required keys, and a
loose `MailChannelsResponse` raises `AttributeError` on whichever fields the
current shape doesn't have, instead of returning `None` like the typed
model does:

```python
client = mailchannels.Client(api_key="...", strict_responses=True)
domain = client.custom_tracking_domains.create(
    name="newsletter-clicks",
    hostname="click.example.com",
    scope="click",
)

if domain.status == "active":
    print(f"{domain.hostname} ready as {domain.name}")
else:
    print(domain.instructions)
    print(domain.txt_record_name, "=", domain.txt_record_value)
```

Add the TXT record alongside the CNAME, wait for propagation, then call
`create()` again with the same `name`/`hostname`/`scope`.

If DNS still isn't in place on retry, MailChannels responds `422` instead of
`202` — that's a real error status, so the SDK raises `InvalidRequestError`
rather than returning a result. The same pending-verification body is on
`error.response`:

```python
try:
    mailchannels.CustomTrackingDomains.create(
        name="newsletter-clicks",
        hostname="click.example.com",
        scope="click",
    )
except mailchannels.InvalidRequestError as error:
    if error.response:
        print(error.response.get("instructions"))
```

## List, Update, Delete

```python
domains = mailchannels.CustomTrackingDomains.list(
    scope="click",       # optional filter
    status="active",     # optional filter: active | disabled
    limit=100,
    offset=0,
)

mailchannels.CustomTrackingDomains.update(
    "click.example.com",
    "click",
    status="disabled",   # or name="new-label" to rename
)

mailchannels.CustomTrackingDomains.delete("click.example.com", "click")
```

Deleting a domain takes effect immediately — tracking links and unsubscribe
URLs already sent using that domain stop working right away. Re-activating a
domain whose DNS verification has since lapsed goes through the same
pending-result flow as `create()`.
