# Sub-Accounts

Sub-accounts are first-class on MailChannels. Use them for tenants,
customers, or isolated senders so that one customer's reputation, limits,
and bad traffic don't contaminate the parent account or other tenants.

> Sub-accounts are only available on parent accounts on the 100K and higher plans.

## Handles

A handle uniquely identifies a sub-account. Rules:

- 3–128 characters.
- **Lowercase alphanumeric only.** No hyphens, underscores, or uppercase.
- Unique per parent account.
- If omitted on create, a random handle is generated.

## Lifecycle

```python
import mailchannels

mailchannels.api_key = "PARENT-ACCOUNT-API-KEY"

# Create
sub = mailchannels.SubAccounts.create(company_name="Client A", handle="clienta")

# List (paginated; default limit 1000)
page = mailchannels.SubAccounts.list(limit=100, offset=0)

# Suspend / activate
mailchannels.SubAccounts.suspend("clienta")
mailchannels.SubAccounts.activate("clienta")

# Delete
mailchannels.SubAccounts.delete("clienta")
```

## Credentials

Each sub-account has its own API keys and SMTP passwords.

```python
# API keys
created_key = mailchannels.SubAccounts.ApiKeys.create("clienta")
# Persist created_key to your secret store; its `id` field (returned as
# an extra on the response) is what you pass to delete later.
keys = mailchannels.SubAccounts.ApiKeys.list("clienta")
mailchannels.SubAccounts.ApiKeys.delete("clienta", "STORED-KEY-ID")

# SMTP passwords
created_password = mailchannels.SubAccounts.SmtpPasswords.create("clienta")
passwords = mailchannels.SubAccounts.SmtpPasswords.list("clienta")
mailchannels.SubAccounts.SmtpPasswords.delete("clienta", "STORED-PASSWORD-ID")
```

**Listed keys and passwords are redacted.** The full secret is only returned
once, at create time. Store it immediately or rotate.

Each sub-account has server-side caps on how many API keys and SMTP
passwords it can hold. Once you hit the cap, `create` raises
`InvalidRequestError` — delete an unused credential first.

## Limits

Per-sub-account monthly send caps. A value of `-1` (returned by GET) means the
sub-account inherits the parent's limit and shares its remaining capacity.

```python
mailchannels.SubAccounts.Limits.set("clienta", sends=100_000)
mailchannels.SubAccounts.Limits.retrieve("clienta")
mailchannels.SubAccounts.Limits.delete("clienta")  # back to inheriting parent
```

The endpoint is **singular** (`/sub-account/{handle}/limit`) and `PUT` takes a
`sends` integer (>= 0). The SDK still accepts the legacy `monthly_limit`
alias on `set()` but new code should use `sends`.

## Usage

```python
parent_usage = mailchannels.Usage.retrieve()
sub_usage = mailchannels.SubAccounts.retrieve_usage("clienta")

print(parent_usage.total_usage, parent_usage.period_start_date, parent_usage.period_end_date)
print(sub_usage.monthly_limit)
```

`Usage.retrieve()` is for the parent. Use `SubAccounts.retrieve_usage(handle)`
when asking about one specific sub-account.

`UsageStats.monthly_limit` (returned by both calls above) is the
*effective* cap already in force for the period — not the same thing as
the `monthly_limit` alias on `Limits.set()` above, which just *sets* a
sub-account's own `sends` limit. A sub-account with no explicit limit set
returns `-1` from `Limits.retrieve()`, but `retrieve_usage(handle)` still
reports the real number in effect (the parent account's limit) rather
than `-1`, so use `monthly_limit` on the usage response — not
`Limits.retrieve()` — for progress-bar-style "X of Y sent" displays.

## Sending As A Sub-Account

Create a separate `Client` with the sub-account's API key. Don't mix it into
the module-level configuration.

```python
client = mailchannels.Client(api_key="SUB-ACCOUNT-API-KEY")

client.emails.queue(
    mailchannels.EmailParams(
        from_=mailchannels.EmailAddress(email="sender@client.example"),
        personalizations=[
            mailchannels.Personalization(
                to=[mailchannels.EmailAddress(email="recipient@example.net")],
            ),
        ],
        subject="From a tenant",
        content=[mailchannels.Content(type="text/plain", value="Hello")],
    )
)
```

This keeps the account boundary explicit in code and avoids hard-to-debug
issues where the wrong key is used at the wrong time.

## Suppressions And Sub-Accounts

When creating suppressions on the parent, pass `add_to_sub_accounts=True` to
also copy the entries into every sub-account. See [suppressions](suppressions.md).
