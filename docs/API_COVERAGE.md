# MailChannels API Coverage

This report is generated from the MailChannels OpenAPI document and the SDK route registry.

- SDK version: `1.2.0`
- OpenAPI source: `https://docs.mailchannels.net/email-api.yaml`
- OpenAPI version: `1.3.0`
- OpenAPI SHA-256: `7cae0bb39ce25ec90e3e5858a014bf6fa00f3d62924c7822568a98f62ba349c2`
- Generated at: `2026-07-03T18:38:59+00:00`

## Summary

- OpenAPI operations: `42`
- SDK-supported operations: `42`
- Pending OpenAPI operations: `0`
- SDK routes absent from OpenAPI: `0`

## Coverage Matrix

| Method | Path | Summary | SDK surface | Sync | Async | Contract test | Online test | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `POST` | `/check-domain` | DKIM, SPF & Domain Lockdown Check | `mailchannels.CheckDomain.check()` | yes | yes | yes | routine | supported |
| `GET` | `/custom-tracking-domains` | Retrieve Custom Tracking Domains | `mailchannels.CustomTrackingDomains.list()` | yes | yes | yes | none | supported |
| `POST` | `/custom-tracking-domains` | Register Custom Tracking Domain | `mailchannels.CustomTrackingDomains.create()` | yes | yes | yes | none | supported |
| `DELETE` | `/custom-tracking-domains/{hostname}/{scope}` | Delete Custom Tracking Domain | `mailchannels.CustomTrackingDomains.delete()` | yes | yes | yes | none | supported |
| `PATCH` | `/custom-tracking-domains/{hostname}/{scope}` | Update Custom Tracking Domain | `mailchannels.CustomTrackingDomains.update()` | yes | yes | yes | none | supported |
| `GET` | `/domains/{domain}/dkim-keys` | Retrieve DKIM Keys | `mailchannels.Dkim.list()` | yes | yes | yes | routine | supported |
| `POST` | `/domains/{domain}/dkim-keys` | Create DKIM Key Pair | `mailchannels.Dkim.create()` | yes | yes | yes | none | supported |
| `PATCH` | `/domains/{domain}/dkim-keys/{selector}` | Update DKIM Key Status | `mailchannels.Dkim.update_status()` | yes | yes | yes | none | supported |
| `POST` | `/domains/{domain}/dkim-keys/{selector}/rotate` | Rotate DKIM Key Pair | `mailchannels.Dkim.rotate()` | yes | yes | yes | none | supported |
| `GET` | `/metrics/engagement` | Retrieve Engagement Metrics | `mailchannels.Metrics.engagement()` | yes | yes | yes | none | supported |
| `GET` | `/metrics/performance` | Retrieve Performance Metrics | `mailchannels.Metrics.performance()` | yes | yes | yes | none | supported |
| `GET` | `/metrics/recipient-behaviour` | Retrieve Recipient Behaviour Metrics | `mailchannels.Metrics.recipient_behaviour()` | yes | yes | yes | none | supported |
| `GET` | `/metrics/senders/{sender_type}` | Retrieve Sender Metrics | `mailchannels.Metrics.senders()` | yes | yes | yes | none | supported |
| `GET` | `/metrics/volume` | Retrieve Volume Metrics | `mailchannels.Metrics.volume()` | yes | yes | yes | routine | supported |
| `POST` | `/send` | Send an Email | `mailchannels.Emails.send()` | yes | yes | yes | routine | supported |
| `POST` | `/send-async` | Send an Email Asynchronously | `mailchannels.Emails.queue()` | yes | yes | yes | none | supported |
| `GET` | `/sub-account` | Retrieve Sub-accounts | `mailchannels.SubAccounts.list()` | yes | yes | yes | routine | supported |
| `POST` | `/sub-account` | Create Sub-account | `mailchannels.SubAccounts.create()` | yes | yes | yes | destructive | supported |
| `DELETE` | `/sub-account/{handle}` | Delete Sub-account | `mailchannels.SubAccounts.delete()` | yes | yes | yes | destructive | supported |
| `POST` | `/sub-account/{handle}/activate` | Activate Sub-account | `mailchannels.SubAccounts.activate()` | yes | yes | yes | destructive | supported |
| `GET` | `/sub-account/{handle}/api-key` | Retrieve Sub-account API Keys | `mailchannels.SubAccounts.ApiKeys.list()` | yes | yes | yes | destructive | supported |
| `POST` | `/sub-account/{handle}/api-key` | Create Sub-account API Key | `mailchannels.SubAccounts.ApiKeys.create()` | yes | yes | yes | destructive | supported |
| `DELETE` | `/sub-account/{handle}/api-key/{id}` | Delete Sub-account API Key | `mailchannels.SubAccounts.ApiKeys.delete()` | yes | yes | yes | destructive | supported |
| `DELETE` | `/sub-account/{handle}/limit` | Delete Sub-account Limit | `mailchannels.SubAccounts.Limits.delete()` | yes | yes | yes | destructive | supported |
| `GET` | `/sub-account/{handle}/limit` | Retrieve Sub-account Limit | `mailchannels.SubAccounts.Limits.retrieve()` | yes | yes | yes | destructive | supported |
| `PUT` | `/sub-account/{handle}/limit` | Set Sub-account Limit | `mailchannels.SubAccounts.Limits.set()` | yes | yes | yes | destructive | supported |
| `GET` | `/sub-account/{handle}/smtp-password` | Retrieve Sub-account SMTP Passwords | `mailchannels.SubAccounts.SmtpPasswords.list()` | yes | yes | yes | destructive | supported |
| `POST` | `/sub-account/{handle}/smtp-password` | Create Sub-account SMTP Password | `mailchannels.SubAccounts.SmtpPasswords.create()` | yes | yes | yes | destructive | supported |
| `DELETE` | `/sub-account/{handle}/smtp-password/{id}` | Delete Sub-account SMTP Password | `mailchannels.SubAccounts.SmtpPasswords.delete()` | yes | yes | yes | destructive | supported |
| `POST` | `/sub-account/{handle}/suspend` | Suspend Sub-account | `mailchannels.SubAccounts.suspend()` | yes | yes | yes | destructive | supported |
| `GET` | `/sub-account/{handle}/usage` | Retrieve Sub-account Usage Stats | `mailchannels.SubAccounts.retrieve_usage()` | yes | yes | yes | none | supported |
| `GET` | `/suppression-list` | Retrieve Suppression List | `mailchannels.Suppressions.list()` | yes | yes | yes | routine, destructive | supported |
| `POST` | `/suppression-list` | Create Suppression Entries | `mailchannels.Suppressions.create()` | yes | yes | yes | destructive | supported |
| `DELETE` | `/suppression-list/recipients/{recipient}` | Delete Suppression Entry | `mailchannels.Suppressions.delete()` | yes | yes | yes | destructive | supported |
| `GET` | `/usage` | Retrieve Usage Stats | `mailchannels.Usage.retrieve()` | yes | yes | yes | routine | supported |
| `DELETE` | `/webhook` | Delete Customer Webhooks | `mailchannels.Webhooks.delete_all()` | yes | yes | yes | destructive | supported |
| `GET` | `/webhook` | Retrieve Customer Webhooks | `mailchannels.Webhooks.list()` | yes | yes | yes | routine, destructive | supported |
| `POST` | `/webhook` | Enroll for Webhook Notifications | `mailchannels.Webhooks.create()` | yes | yes | yes | destructive | supported |
| `GET` | `/webhook-batch` | Retrieve Webhook Batches | `mailchannels.Webhooks.batches()` | yes | yes | yes | none | supported |
| `POST` | `/webhook-batch/{batch_id}/resend` | Resend Events | `mailchannels.Webhooks.resend_batch()` | yes | yes | yes | none | supported |
| `GET` | `/webhook/public-key` | Retrieve Webhook Signing Key | `mailchannels.Webhooks.public_key()` | yes | yes | yes | none | supported |
| `POST` | `/webhook/validate` | Validate Enrolled Webhook | `mailchannels.Webhooks.validate()` | yes | yes | yes | destructive | supported |

## Notes

- `Contract test` is `yes` because `tests/test_openapi_request_contract.py` asserts that every SDK route has an executable request contract.
- `Online test` is `routine` for non-mutating manual live tests, `destructive` for manually gated lifecycle tests, and `none` when only local contract coverage exists.
- This report intentionally tracks endpoint coverage first. Request-field and response-field coverage can be added after strict response model coverage is complete.
