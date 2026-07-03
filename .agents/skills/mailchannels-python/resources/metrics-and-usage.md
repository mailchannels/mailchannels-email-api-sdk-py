# Metrics And Usage

The metrics resource exposes the operational view of your traffic. Usage
exposes billing-period totals.

## Time-Series Metrics

The four time-series methods share the same parameter shape: optional
`start_time`, `end_time`, `campaign_id`, and `interval`. (`Metrics.senders()`
is grouped data with a different signature — see below.)

```python
import mailchannels

mailchannels.Metrics.volume(
    start_time="2026-04-01",
    end_time="2026-05-01T00:00:00Z",
    interval="day",        # hour | day | week | month (default day)
    campaign_id="welcome", # optional filter
)

# Same parameter shape — pass the same kwargs to any of these:
mailchannels.Metrics.engagement(interval="day")          # open / click counts
mailchannels.Metrics.performance(interval="day")         # delivered / bounced / complained / processed
mailchannels.Metrics.recipient_behaviour(interval="day") # unsubscribes — British spelling matches the endpoint
```

Time formats accepted: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`. Defaults:
`start_time` is one month ago, `end_time` is now.

### Unique open/click counts

`engagement()` also returns `unique_open`, `unique_click`,
`unique_open_tracking_delivered`, and `unique_click_tracking_delivered`.
These count each message at most once regardless of how many times it was
opened or clicked, so they're the correct numerator/denominator for open and
click rates — `open`/`click` can overcount and produce rates above 100%.

```python
engagement = mailchannels.Metrics.engagement(interval="day")
unique_opened = engagement.unique_open
unique_delivered = engagement.unique_open_tracking_delivered

if unique_opened is not None and unique_delivered:
    unique_open_rate = unique_opened / unique_delivered
```

### Buckets

Each response includes both totals **and** a `buckets` object grouped by
metric name, each containing a list of `{period_start, count}` rows aligned to
`interval`.

```python
result = mailchannels.Metrics.volume(interval="day")

for bucket in result.buckets.processed:
    print(bucket.period_start, bucket.count)
```

## Sender Metrics

`senders()` lists per-sender totals grouped either by campaign or sub-account.

```python
campaigns = mailchannels.Metrics.senders(
    "campaigns",        # required: "campaigns" or "sub-accounts"
    start_time="2026-04-01",
    end_time="2026-05-01",
    limit=50,           # 1..1000, default 10
    offset=0,
    sort_order="desc",  # asc | desc, default desc, by processed+dropped
)

for sender in campaigns.senders:
    print(sender.name, sender.processed, sender.bounced)
```

Senders with **zero traffic in the time range are omitted** from the
response.

## Usage

Use `Usage.retrieve()` for parent-account usage in the current billing
period:

```python
usage = mailchannels.Usage.retrieve()

print(usage.total_usage)          # int, messages sent this period
print(usage.period_start_date)    # ISO date
print(usage.period_end_date)
```

For a specific sub-account, use `SubAccounts.retrieve_usage(handle)` instead.
See [sub-accounts](sub-accounts.md).

## Common Patterns

- **Daily dashboard**: `Metrics.volume(interval="day")` plus
  `Metrics.engagement(interval="day")` over the same range.
- **Campaign post-mortem**: pass `campaign_id` on each call, then read both
  totals and buckets.
- **Top senders by sub-account**: `Metrics.senders("sub-accounts",
  sort_order="desc")`.
- **Billing reconciliation**: `Usage.retrieve()` plus each sub-account's
  `SubAccounts.retrieve_usage(handle)` should sum within the parent's limit.
