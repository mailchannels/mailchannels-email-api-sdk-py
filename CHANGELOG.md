# Changelog

All notable changes to the MailChannels Python SDK are recorded here. The
format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project adheres to [Semantic Versioning](https://semver.org/). Until
`1.0.0` the public API may still change between minor releases; from `1.0.0`
onward, breaking changes will require a major version bump.

## [Unreleased]

Reserved for in-progress work targeting the next release.

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

- **Development status: Beta.** The public API is feature-complete and
  stable in practice, but `1.0.0` will be the formal stability
  commitment. Minor releases between now and `1.0.0` may still adjust
  ergonomics in response to early-adopter feedback.
- `Webhooks.delete_all()` is intentionally explicit about its bulk-delete
  semantic. The underlying `DELETE /webhook` removes every configured
  endpoint for the account — there is no per-endpoint delete in the API.
- Sending methods come in four variants by design: `send()` / `queue()`
  describe the **server-side** distinction (`/send` versus
  `/send-async`); the `_async` suffix is the unrelated **client-side**
  Python asyncio distinction. See the README "Send vs Queue, And The Two
  Meanings of Async" section for guidance.

[Unreleased]: https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/branches/compare/main..v0.1.2
[0.1.2]: https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/v0.1.2
[0.1.1]: https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/v0.1.1
