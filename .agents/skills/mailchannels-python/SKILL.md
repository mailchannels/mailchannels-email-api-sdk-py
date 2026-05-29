---
name: mailchannels-python
description: Python SDK for the MailChannels Email API (PyPI `mailchannels`; `import mailchannels`). Use when sending or queueing email, working with attachments, mustache templates, unsubscribe, custom headers, DKIM keys, sub-accounts, domain checks, metrics, usage, suppressions, or webhooks (incl. signature verification); also configuring clients & custom HTTP transports, asyncio (`*_async` methods), dict-like vs strict Pydantic responses, and error handling. Skip when (a) developing the SDK itself — defer to the repo's root AGENTS.md; (b) the user is in a non-Python language — MailChannels publishes separate SDKs for other ecosystems and the Python types/idioms here don't apply.
---

# MailChannels Python SDK

This skill helps you write **Python** code that uses the `mailchannels`
package (PyPI: `mailchannels`, importable as `import mailchannels`). It is
specific to the official Python SDK — MailChannels publishes separate SDKs
for other languages and their APIs differ.

> **Scope.** This skill is for *consuming* the Python SDK from application
> code. Working **on** the SDK (adding features, fixing bugs, releasing
> the package) is a different job — defer to the repo's root `AGENTS.md`
> for dev rules in that case. If the user is working in a non-Python
> language, this skill does not apply — use the MailChannels skill for
> that language's SDK, or fall back to the raw HTTP API.

### Quick Sanity Check Before Using This Skill

If any of these are true, you're in the right place:

- The file you're editing ends in `.py`, `.pyi`, or `.ipynb`.
- The user said "Python", "pip", "uv", "poetry", `requirements.txt`,
  `pyproject.toml`, FastAPI, Flask, Django, Starlette, Celery, or
  asyncio.
- The codebase already imports `mailchannels` or has `mailchannels` in
  its dependencies.

If the user is in a JavaScript / TypeScript / Node, Go, Ruby, PHP, Rust,
or shell context, stop and pick the correct MailChannels skill for that
language (or use the HTTP API directly). The Python SDK's class names,
method casing, and dict-shaped payloads are Python conventions and don't
carry over.

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
│   └── …from asyncio code (FastAPI, Starlette, aiohttp, …)?
│       → resources/async.md
│
├── Manage hosted DKIM keys (create / list / rotate / revoke)
│   → resources/dkim.md
│
├── Validate a sender domain's auth posture (DKIM/SPF/Lockdown/DNS)
│   → resources/domain-checks.md
│
├── Multi-tenant work — sub-accounts, their credentials, limits, usage
│   → resources/sub-accounts.md
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
