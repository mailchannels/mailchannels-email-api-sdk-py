# Suppressions

A suppression list keeps known-bad or opted-out recipients out of future
sends. MailChannels suppresses by recipient + suppression type + source.

## Create Entries

```python
import mailchannels

mailchannels.Suppressions.create(
    [
      mailchannels.suppressions.types.SuppressionEntryParams(
            recipient="out@example.net",
            suppression_types=["non-transactional"],   # optional; defaults to non-transactional
            notes="Imported from preference center",   # optional, max 1024 chars
      ),
      mailchannels.suppressions.types.SuppressionEntryParams(
            recipient="complainer@example.net",
            suppression_types=["transactional", "non-transactional"],
        ),
    ],
    add_to_sub_accounts=True,   # parent only; copies entries to every sub-account
)
```

Constraints:

- **Atomic**: either every entry in the request is added, or none are.
- A single request can carry at most **1000** entries combined across the
  parent and any sub-accounts.
- Each `recipient` is up to 255 characters; `notes` up to 1024.
- `suppression_types` items must be `transactional` or `non-transactional`.

If any entry already exists, the API returns **409 Conflict**.

## List Entries

```python
entries = mailchannels.Suppressions.list(
    recipient="recipient@example.net",   # exact-match filter
    source="api",                         # see source values below
    created_after="2026-04-01",
    created_before="2026-05-01T00:00:00Z",
    limit=100,                            # 1..1000, default 1000
    offset=0,
)
```

`source` values:

- `api` — explicitly created by you (or your code) via this endpoint.
- `unsubscribe_link` — recipient used the hosted unsubscribe URL.
- `list_unsubscribe` — recipient used a one-click `List-Unsubscribe` header.
- `hard_bounce` — bounced as undeliverable.
- `spam_complaint` — recipient reported spam at their provider.

Date formats accepted: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`.

## Delete An Entry

```python
mailchannels.Suppressions.delete("recipient@example.net", source="api")
mailchannels.Suppressions.delete("recipient@example.net", source="all")
```

If `source` is omitted it defaults to `api`. Use `source="all"` to remove
every suppression for that recipient regardless of origin.

## Patterns

- **Preference center opt-out**: write `source="api"`, type
  `non-transactional`, with `notes` pointing back to the row in your
  preference DB.
- **Migrating from another ESP**: bulk-create with `source="api"` and
  `add_to_sub_accounts=True` so every tenant inherits the list.
- **Re-engagement campaign**: list with `source="hard_bounce"` and your
  re-engagement filter; only resurrect recipients you've manually verified.
