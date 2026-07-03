# Custom Tracking Domains

By default, MailChannels rewrites click tracking links, open tracking pixels,
and unsubscribe URLs to use shared `mailchannels.net` domains. Registering a
custom tracking domain lets you replace those shared domains with your own
branded hostname (e.g. `click.example.com`) for one of three scopes: `click`,
`open`, or `unsubscribe`.

## Register A Domain

Registration needs a CNAME record in place before it can complete:

```python
domain = mailchannels.CustomTrackingDomains.create(
    name="newsletter-clicks",     # label used to select this domain at send time
    hostname="click.example.com",
    scope="click",
)
```

Add a CNAME record for `click.example.com` pointing to
`links.mailchannels.net` before calling `create()`.

## DNS Ownership Verification

The first time a hostname is registered, MailChannels also requires proving
ownership via a TXT record — and the verification token for that TXT record
is generated and returned *by* the first `create()` call, so a brand-new
hostname can never come back active on that first call. `create()` (and
`update()`, when re-activating a disabled domain) return a pending result
instead — both shapes come back through the same `CustomTrackingDomainResult`
model, so check which fields are present rather than assuming success:

```python
domain = mailchannels.CustomTrackingDomains.create(
    name="newsletter-clicks",
    hostname="click.example.com",
    scope="click",
)

if domain.get("status") == "active":
    print(f"{domain['hostname']} is ready to use as {domain['name']}")
else:
    print(domain.get("instructions"))
    print("Add this TXT record:")
    print(" ", domain.get("txt_record_name"), "=", domain.get("txt_record_value"))
```

Add the TXT record described in `txt_record_name`/`txt_record_value`
alongside the CNAME record, wait for DNS propagation, then call `create()`
again with the same `name`/`hostname`/`scope` to complete registration.

If the DNS records still aren't in place when you retry, MailChannels
returns a `422` instead of a `202` — the SDK raises `InvalidRequestError` for
that response, with the same pending-verification body available on
`error.response`:

```python
try:
    domain = mailchannels.CustomTrackingDomains.create(
        name="newsletter-clicks",
        hostname="click.example.com",
        scope="click",
    )
except mailchannels.InvalidRequestError as error:
    print(error.response.get("instructions"))
```

## Use A Custom Domain At Send Time

Once a domain is active, select it by `name` in `tracking_settings` (for
click/open tracking) or `unsubscribe_settings` (for unsubscribe links):

```python
mailchannels.Emails.queue(
    {
        "from": {"email": "sender@example.com"},
        "to": "recipient@example.net",
        "subject": "Newsletter",
        "text": "Hello",
        "tracking_settings": {
            "click_tracking": {
                "enable": True,
                "custom_domain_name": "newsletter-clicks",
            },
            "open_tracking": {"enable": True},
        },
        "unsubscribe_settings": {"custom_domain_name": "newsletter-unsubscribe"},
    }
)
```

`custom_domain_name` must name a domain that is currently `active` for that
scope — the API contract doesn't document what happens if it names a domain
that's still pending verification or disabled, so don't rely on a specific
fallback behavior; verify the domain is `active` before referencing it in a
send.

## Manage Registered Domains

```python
domains = mailchannels.CustomTrackingDomains.list(scope="click", status="active")

mailchannels.CustomTrackingDomains.update(
    "click.example.com",
    "click",
    status="disabled",
)

mailchannels.CustomTrackingDomains.delete("click.example.com", "click")
```

`update()` can rename a domain (`name=`) or toggle it between `active` and
`disabled`; re-activating a domain that was disabled long enough to lose DNS
verification returns the same pending-verification shape as `create()`.

Deleting a domain takes effect immediately — tracking links and unsubscribe
URLs in previously sent emails that reference the deleted domain will stop
working right away.
