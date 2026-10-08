---
name: mailchannels-python
description: Python SDK for the MailChannels Email API (PyPI `mailchannels`; `import mailchannels`). Use when sending or queueing email, working with attachments, mustache templates, unsubscribe, custom headers, custom tracking domains, DKIM keys, sub-accounts, domain checks, metrics, usage, suppressions, or webhooks (incl. signature verification); also configuring clients & custom HTTP transports, asyncio (`*_async` methods), dict-like vs strict Pydantic responses, and error handling. Skip when (a) developing the SDK itself — defer to the repo's root AGENTS.md; (b) the user is in a non-Python language — MailChannels publishes separate SDKs for other ecosystems and the Python types/idioms here don't apply.
---

# MailChannels Python SDK

This skill helps you write **Python** code that uses the `mailchannels`
package (PyPI: `mailchannels`, importable as `import mailchannels`). It is
specific to the official Python SDK — MailChannels publishes separate SDKs
for other languages and their APIs differ.

> **Scope.** This skill is for *consuming* the Python SDK from application
> code. Working **on** the SDK (adding features, fixing bugs, releasing
> the package) is a different job — defer to the repo's root `AGENTS.md`
> for development rules and the Bitbucket pull-request workflow.
> If the user is working in a non-Python
> language, this skill does not apply — use the MailChannels skill for
> that language's SDK, or fall back to the raw HTTP API.

## How To Use This Skill

The body of each topic lives in [`resources/`](resources/). Read this file
for context and the decision tree, then load only the resource files that
match the task. Don't preload everything.

### Decision Tree

Start at the top; descend until you hit a leaf, then read the linked
resource. If multiple branches apply (e.g. "send + attachments + async"),
read each leaf.

```
You're about to write Python SDK code. What does it need to do?

├── Get oriented — what is the SDK, what are the entry points?
│   → resources/overview.md
│
├── Set up the client (API keys, base URL, multi-tenant, lifecycle,
│   custom HTTP transports)
│   → resources/clients-and-transport.md
│
├── Send email
│   → resources/sending.md
│   ├── …with file / bytes / URL / inline-image attachments?
│   │   → resources/attachments.md
│   ├── …with a mustache template + per-recipient data?
│   │   → resources/templates.md
│   ├── …with an unsubscribe link or List-Unsubscribe header?
│   │   → resources/unsubscribe.md
│   ├── …with custom X-… headers?
│   │   → resources/custom-headers.md
│   ├── …with a custom tracking/unsubscribe domain?
│   │   → resources/custom-tracking-domains.md
│   └── …from asyncio code (FastAPI, Starlette, aiohttp, …)?
│       → resources/async.md
│
├── Register or manage custom tracking domains (click/open/unsubscribe)
│   → resources/custom-tracking-domains.md
│
├── Manage hosted DKIM keys (create / list / rotate / revoke)
│   → resources/dkim.md
│
├── Validate a sender domain's auth posture (DKIM/SPF/Lockdown/DNS)
│   → resources/domain-checks.md
│
├── Multi-tenant work — sub-accounts, their credentials, limits, usage
│   → resources/sub-accounts.md
|
├── Query analytics (volume, engagement, performance, senders) or
│   current-period usage
│   → resources/metrics-and-usage.md
│
├── Manage the suppression list (list, create, delete)
│   → resources/suppressions.md
│
├── Receive or manage delivery-event webhooks (enroll, validate,
│   inspect batches, verify signatures)
│   → resources/webhooks.md
│
├── Catch / log / retry SDK or API errors
│   → resources/error-handling.md
│
└── Get strict Pydantic response models instead of dict-like responses
    → resources/responses.md
```

## Style Conventions In The Resources

- Every resource is **Python**: code blocks are Python, types referenced
  by name (Pydantic models, exceptions, transport protocols) are the
  ones exported by the `mailchannels` package on PyPI.
- Resource examples use the **typed Pydantic models** (`EmailParams`,
  `EmailAddress`, `Personalization`, `Content`, `Attachment`, …) for
  send payloads — they validate at construction time and produce code
  that's straightforward for both humans and type checkers to verify.
  The SDK also accepts plain dictionaries (`SendParams` TypedDict) when
  brevity matters more than validation.
- All recipient and sender addresses use the IANA-reserved `example.com`
  / `example.net` domains. Replace before running.

## Beyond This Skill

When a resource leaves something ambiguous, the SDK source itself is the
final authority — exported names, signatures, and docstrings live in the
installed `mailchannels` package (e.g. `python -c "import mailchannels;
help(mailchannels.Emails.queue)"`). The published `mailchannels` package
on PyPI also ships with its own README and reference docs.
