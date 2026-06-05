# Changelog

All notable changes to the MailChannels Python SDK are recorded here. The
format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project adheres to [Semantic Versioning](https://semver.org/). Until
`1.0.0` the public API may still change between minor releases; from `1.0.0`
onward, breaking changes will require a major version bump.

## [Unreleased]

Reserved for in-progress work targeting the next release.

## [1.0.0] - 2026-06-05

First stable release. From this point forward, breaking changes to the
public API require a major version bump per semantic versioning. The
public surface — clients, resources, response models, exceptions, helpers,
and the strict-response opt-in — is now considered stable.

### Removed

- **Breaking:** `Attachment.from_file()`, `Attachment.from_url()`, and
  `Attachment.inline_file()` have been removed. A generic file-reader and
  URL-fetcher cannot make safe trust-boundary decisions on the caller's
  behalf — `from_file` is exposed to arbitrary local-file disclosure when
  the path comes from untrusted input, and `from_url` is a ready-made SSRF
  primitive. The corresponding `MailChannelsError` codes
  `AttachmentReadError` and `AttachmentFetchError` are gone as well. The
  remaining `Attachment.from_bytes()` factory covers every prior use case
  once the caller has loaded the bytes themselves with whatever validation
  their context requires. `Attachment.inline_file()` also relied on
  upstream API support for `disposition: inline` and `content_id` that
  the public Email API does not actually honour today, so removing it
  also fixes a silent no-op. These factories may return in a future
  release once a safe loading contract has been designed.

### Changed

- **Breaking:** Aligned response models with the public OpenAPI contract
  (`public.yaml`). Several fields were previously typed as `X | None = None`
  even though the contract marks them required, and three response classes
  were declared with no typed fields at all (relying on `extra="allow"`).
  Callers can now drop defensive `None` checks on guaranteed fields, but
  code that destructured these models with `None` fallbacks will need to
  adjust.
  - `SubAccount.handle` is now `str` (was `str | None`). Required in
    `SubAccountDetails`.
  - `SubAccount.enabled` is now `bool` (was `bool | None`). Required in
    `SubAccountDetails`.
  - `WebhookResendResponse.customer_handle` is now `str` (was `str | None`).
    Required in `WebhookResendResponse`.
  - `WebhookValidationResult.response` is now `WebhookValidationResponse |
    None` with no default — the field is required to be present but may be
    `null` when the webhook endpoint did not respond.
  - `ApiKey` now exposes typed `id: int | None` and `key: str | None`
    fields (previously had no declared fields).
  - `SmtpPassword` now exposes typed `id: int | None`, `enabled: bool |
    None`, and `smtp_password: str | None` fields (previously had no
    declared fields).
  - `mailchannels.sub_accounts.UsageStats` is now an alias for the existing
    `mailchannels.usage.UsageStats` — both endpoints return the same shape
    per the contract, so the SDK now exposes one shared model with
    `total_usage: int` (required), `period_start_date: str | None`, and
    `period_end_date: str | None`.

## [0.1.3] - 2026-05-29

### Added

- AI Agent Skill in .agents directory. Can be installed by customers to help
  their AI agents interact with the MailChannels Email API.

### Changed

- When using pydantic types, `EmailParams` and `Personalizations` models now
  properly accept the `from_` field without having to pass args via `.model_validate()`

## [0.1.2] - 2026-05-26

### Added

- `NotFoundError` exception class for 404 responses. Carries
  `error_type = "not_found"` and a suggested-action hint pointing the caller
  at the resource identifier. Exported from `mailchannels` and surfaced in
  the API reference.

### Changed

- **Breaking:** 404 responses now raise `NotFoundError` instead of
  `InvalidRequestError`. Callers that previously caught `InvalidRequestError`
  to handle missing-resource cases — for example, `webhooks.resend_batch`
  against an unknown `batch_id` — must add `except NotFoundError` (or catch
  the shared `ApiError` parent). The previous mapping treated a missing
  resource as a malformed request, which prevented callers from
  distinguishing the two.

## [0.1.1] - 2026-05-21

Initial public release on PyPI. Built and tested against MailChannels Email
API `0.21.1`.

### Added

- Synchronous and asynchronous clients for the MailChannels Email API. Full
  parity between every `method()` and its `method_async()` counterpart.
- Resource coverage for `/send`, `/send-async`, `/check-domain`, hosted DKIM
  keys, sub-accounts (create, list, suspend, activate, delete, usage), API
  keys, SMTP passwords, sending limits, suppression list, metrics (volume,
  engagement, performance, recipient behaviour, sender), parent-account
  usage, webhooks (list, enrol, delete-all, batches, public-key, validate,
  resend), and webhook signature verification (RFC 9421 Ed25519).
- Module-level convenience accessors (`mailchannels.Emails.send(...)`,
  `mailchannels.Webhooks.list()`, etc.) for scripts and small applications,
  plus per-`Client` accessors for multi-tenant code that needs separate
  credentials per request.
- Strict response models via the `strict_responses=True` flag: every
  operation returns a typed Pydantic model when enabled, including
  `EmptyResponse` for the 204/no-body mutations.
- Helpers to attach files via `Attachment.from_file()`,
  `Attachment.from_bytes()`, `Attachment.from_url()`, and
  `Attachment.inline_file()` so MailChannels' Base64 + MIME conventions are
  handled automatically.
- Typed exception hierarchy (`AuthenticationError`, `ForbiddenError`,
  `RateLimitError`, `PayloadTooLargeError`, `ConflictError`,
  `InvalidRequestError`, `ServerError`, `BadGatewayError`,
  `ResponseValidationError`, `ConfigurationError`) with structured metadata
  (`status_code`, `code`, `request_id`, `retry_after`, `suggested_action`).
- Custom transport support: any object satisfying `SyncHTTPClient` or
  `AsyncHTTPClient` can replace the default `requests` / `httpx`
  transports, for instrumentation, retries, or test doubles.
- Module-level configuration via `mailchannels.api_key`,
  `mailchannels.base_url`, `MAILCHANNELS_API_KEY`, and
  `MAILCHANNELS_API_URL`.
- Tested examples under `examples/` covering async sending, attachments,
  templates, unsubscribe, custom headers, DKIM (including a Cloudflare DNS
  publication walkthrough), sub-accounts, metrics, domain checks,
  suppressions, webhooks, usage, custom HTTP clients, and structured error
  handling.

### Notes

- `Webhooks.delete_all()` is intentionally explicit about its bulk-delete
  semantic. The underlying `DELETE /webhook` removes every configured
  endpoint for the account — there is no per-endpoint delete in the API.
- Sending methods come in four variants by design: `send()` / `queue()`
  describe the **server-side** distinction (`/send` versus
  `/send-async`); the `_async` suffix is the unrelated **client-side**
  Python asyncio distinction. See the README "Send vs Queue, And The Two
  Meanings of Async" section for guidance.

[Unreleased]: https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/branches/compare/main..v1.0.0
[1.0.0]: https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/v1.0.0
[0.1.3]: https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/v0.1.3
[0.1.2]: https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/v0.1.2
[0.1.1]: https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/v0.1.1
