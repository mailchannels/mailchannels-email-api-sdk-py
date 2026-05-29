# Domain Checks

Use `CheckDomain.check()` to confirm a sender domain is properly authenticated
before sending from it. The check covers four things:

- **DKIM** — does the domain publish a DKIM public key matching the
  selectors MailChannels signs with?
- **SPF** — is MailChannels in the domain's SPF record?
- **Sender-domain DNS** — does the domain have at least one of an `A` or
  `MX` record? Receivers reject mail without either as **SDNF**
  ("Sender Domain Not Found"); the check catches this before sends start
  bouncing.
- **Domain Lockdown** — a MailChannels feature that ties a sending domain
  to your account so other MailChannels customers cannot spoof it. The
  check confirms the lockdown association is in place.

## Basic Check

```python
import mailchannels

result = mailchannels.CheckDomain.check("example.com")

# `result.check_results` and each sub-result are Optional — guard them
# (or use `getattr`) before reading verdicts.
checks = result.check_results
if checks is not None:
    if checks.spf is not None:
        print(checks.spf.verdict)             # passed | failed | …
    if checks.domain_lockdown is not None:
        print(checks.domain_lockdown.verdict) # passed | failed
    if checks.sender_domain is not None:
        print(checks.sender_domain.verdict)   # passed | failed
    print(checks.dkim)                        # list[DkimResult] | None

print(result.references)                      # support links if anything failed
```

## With Specific DKIM Settings

If you don't pass any `dkim_settings`, MailChannels uses all stored keys for
the domain. To target a specific selector:

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

You can pass up to **10** DKIM settings per call.

### DKIM settings resolution rules

The API resolves `dkim_settings` items as follows:

| Provided fields | Behavior |
| --- | --- |
| `dkim_domain`, `dkim_selector`, `dkim_private_key` all present | Verify with the provided key. |
| `dkim_domain`, `dkim_selector` | Use the stored private key for that domain + selector. |
| `dkim_domain` only | Use **all** stored keys for that domain. |
| `dkim_selector` only | Use the `domain` from the request body. |
| `dkim_private_key` set | `dkim_selector` is required too. |
| `dkim_settings` empty / absent | Use all stored keys for the request `domain`. |

## Verdicts Reference

DKIM, Domain Lockdown, A, and MX verdicts are each `passed` or `failed`.

SPF has a richer set: `passed`, `failed`, `soft failed`, `temporary error`,
`permanent error`, `neutral`, `none`, or `unknown`.

`sender_domain` overall passes if **either** the A or MX check passes. The
component verdicts are nested under `result.check_results.sender_domain.a`
and `…sender_domain.mx`.

## Domain Lockdown

Domain Lockdown ties a sending domain to your MailChannels account so
other customers can't spoof from it. Setup is a single DNS TXT record at
`_mailchannels.<domain>` whose value is a space-separated field list
beginning with `v=mc1`. Three field types are accepted:

| Field | Effect |
| --- | --- |
| `auth=<account-id>` | Authorizes an entire MailChannels account to send from this domain. |
| `senderid=<account>\|<type>\|<sender>` | Authorizes one exact sender identity. |
| `sidw=<account>\|<type>\|<pattern>` | Same as `senderid`, but the pattern may contain `*` wildcards. |

Multiple fields can coexist in the record; a message passes lockdown if
any one matches. Full setup details, including how to obtain the account
ID and verify propagation, live in the [Domain Lockdown
docs][lockdown-docs].

The SDK exposes one lockdown-related knob: the `sender_id` argument on
`CheckDomain.check()`. Use it **only** when your lockdown record relies
on `senderid=` or `sidw=` fields — pass the sender identity you expect to
match (the same value that appears in the `X-MailChannels-SenderId`
header on outgoing mail):

```python
result = mailchannels.CheckDomain.check(
    "example.com",
    sender_id="example|domain|example.com",
)
```

If your lockdown record uses `auth=` (account-wide authorization), omit
`sender_id` and call `CheckDomain.check("example.com")` with just the
domain.

[lockdown-docs]: https://docs.mailchannels.net/email-api/advanced/domain-lockdown/

## When To Use

- During onboarding for every new sending domain.
- In CI after rotating DKIM keys, to verify the new DNS record propagated.
- In a periodic monitoring job (the verdicts can drift if DNS changes).
