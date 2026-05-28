# DKIM Keys

MailChannels can host the **private** DKIM key for you. You publish the
**public** key in the domain's DNS as a TXT record. The public DNS record is
**not** hosted by MailChannels — you must publish it yourself in whatever DNS
provider holds the zone (e.g. Route53, Cloudflare).

## Create A Hosted Key

```python
import mailchannels

key = mailchannels.Dkim.create(
    "example.com",
    selector="mcdkim",
    algorithm="rsa",        # only "rsa" is currently supported
    key_length=2048,        # 1024 or 2048; default 2048; multiples of 1024
)

for record in key.dkim_dns_records or []:
    print(record.name, record.type, record.value)
```

The returned `key.dkim_dns_records` contains TXT records you must publish.

## List, Filter, And Include DNS Records

```python
keys = mailchannels.Dkim.list(
    "example.com",
    selector="mcdkim",         # optional; returns at most one
    status="active",           # active | retired | revoked | rotated
    include_dns_record=True,   # include suggested DNS record per key
    limit=10,
    offset=0,
)
```

## Lifecycle

A DKIM key has one of four statuses:

| Status | Meaning |
| --- | --- |
| `active` | Currently used for signing. |
| `rotated` | Being rotated out. Still valid for signing for a 3-day grace period; auto-changes to `retired` 2 weeks after rotation. |
| `retired` | No longer in use. |
| `revoked` | Marked compromised. Stop using immediately. |

### Update status directly

```python
mailchannels.Dkim.update_status("example.com", selector="mcdkim", status="revoked")
```

Only `revoked`, `retired`, and `rotated` are valid update targets. Only
`active` keys can move to `rotated`.

### Rotate (recommended for routine rollover)

```python
result = mailchannels.Dkim.rotate(
    "example.com",
    "mcdkim",                # old selector — marked rotated
    new_selector="mcdkim2",  # selector for the freshly-issued key
)

# result.new_key is the new DkimKeyInfo; result.rotated_key is the old one.
# `gracePeriodExpiresAt` on the rotated key says when signing with it stops.
```

Rotation:

1. Marks the existing key `rotated` (still valid for **3 days** — exact
   cut-off in `gracePeriodExpiresAt`).
2. Creates a new active key with the new selector, reusing the same
   algorithm and key length.
3. The rotated key is auto-retired **2 weeks** after rotation (exact
   moment in `retiresAt`).

**Publish the new DNS record before `gracePeriodExpiresAt`** or emails
signed with the new key will fail DKIM at receiving providers.

## Sending With A Hosted Key

```python
mailchannels.Emails.queue(
    mailchannels.EmailParams(
        from_=mailchannels.EmailAddress(email="sender@example.com"),
        personalizations=[
            mailchannels.Personalization(
                to=[mailchannels.EmailAddress(email="recipient@example.net")],
            ),
        ],
        subject="Signed",
        content=[
            mailchannels.Content(type="text/plain", value="Signed by hosted DKIM"),
        ],
        dkim_domain="example.com",
        dkim_selector="mcdkim",
    )
)
```

If `dkim_selector` is set without `dkim_domain`, MailChannels takes the
domain from `from.email`.

## Sending With A Customer-Managed Key

If you keep the private key yourself, pass it Base64-encoded:

```python
mailchannels.Emails.queue(
    mailchannels.EmailParams(
        from_=mailchannels.EmailAddress(email="sender@example.com"),
        personalizations=[
            mailchannels.Personalization(
                to=[mailchannels.EmailAddress(email="recipient@example.net")],
            ),
        ],
        subject="Signed",
        content=[
            mailchannels.Content(type="text/plain", value="Signed by my own DKIM key"),
        ],
        dkim_domain="example.com",
        dkim_selector="mcdkim",
        dkim_private_key="<base64-encoded-private-key>",
    )
)
```

Any of `dkim_domain` / `dkim_selector` / `dkim_private_key` can be set per
personalization to override the root values.

## DNS Publication

MailChannels does not host the public DKIM DNS record — you do. The SDK
returns the exact record to publish in `dkim_dns_records`:

```python
key = mailchannels.Dkim.create("example.com", selector="mcdkim")

for record in key.dkim_dns_records or []:
    print(record.name, record.type, record.value)
    # e.g.  mcdkim._domainkey.example.com  TXT  "v=DKIM1; k=rsa; p=MIIBIj..."
```

Every record has the same shape across every DNS provider:

| Field | Value |
| --- | --- |
| `name` | The DNS host. Always `{selector}._domainkey.{domain}`. |
| `type` | Always `TXT`. |
| `value` | The public key material as a quoted TXT string. **Publish the value verbatim** — do not re-wrap, strip quotes, or split lines. Providers that store TXT values without quotes will display the contents without the surrounding `"`s; that's fine, just don't alter the bytes. |

### Required Steps

The provider-specific code differs, but the same six steps apply everywhere:

1. **Generate the key** with `mailchannels.Dkim.create(domain,
   selector=...)`. Capture the returned `dkim_dns_records`.
2. **Resolve the DNS zone** that hosts `domain` in your provider's API.
3. **Look up any existing TXT record** at `dns_record["name"]` in that
   zone so the publication is idempotent.
4. **Create or update** the TXT record with `content = dns_record["value"]`.
   Use a short TTL (300 s, or your provider's "automatic" setting) so
   future rotations propagate quickly.
5. **Wait for propagation**, then verify with
   `mailchannels.CheckDomain.check(domain, dkim_settings=[
   mailchannels.DkimSetting(dkim_selector=selector)])`. The `dkim` verdict
   must be `passed` before you start signing real traffic with the
   selector.
6. **For rotations**, leave the rotated key's TXT record in place until
   `gracePeriodExpiresAt` on the old key has passed (the SDK exposes this
   in the rotation response). Publishing the new record before the old
   one expires keeps in-flight mail valid throughout the cutover.

### Provider-Side Permissions

Whatever provider you use, the credentials should be scoped to the
narrowest workable role — typically **read zones + read/write DNS records
on the target zone only**. A broader token (full DNS edit across every
zone) is unnecessary and a larger blast radius if leaked.

### Choosing The Right Record In Multi-Record Responses

`dkim_dns_records` is a list because some algorithms or migration states
can return more than one record. When it has multiple entries, publish
**all** of them under the names provided — partial publication will fail
verification.

## Selector Format

- 1–63 characters.
- Lowercase letters, numbers, and `-` work everywhere. Avoid `_` in the
  selector itself; it's only used in the DNS host name.
