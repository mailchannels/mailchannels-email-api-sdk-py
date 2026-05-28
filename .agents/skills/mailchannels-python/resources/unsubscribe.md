# Unsubscribe

MailChannels offers two **complementary** unsubscribe mechanisms — an
in-body unsubscribe link, and the standard `List-Unsubscribe` /
`List-Unsubscribe-Post` headers. They are not alternatives. A
non-transactional (bulk / marketing / notification) send should use
**both**: the headers let inbox providers surface a one-click
"Unsubscribe" button in their UI, and the in-body link is what
recipients actually see and click inside the message body. Major inbox
providers (Gmail, Yahoo, etc.) effectively require both for bulk
senders.

Both mechanisms require the message to have **exactly one recipient per
personalization** and to be **DKIM-signed**.

## In-Body Unsubscribe Link

Use `UNSUBSCRIBE_URL_PLACEHOLDER` inside mustache HTML content.
MailChannels substitutes a hosted one-click unsubscribe URL at render
time.

```python
import mailchannels

mailchannels.Emails.queue(
    mailchannels.EmailParams(
        from_=mailchannels.EmailAddress(email="sender@example.com"),
        personalizations=[
            mailchannels.Personalization(
                to=[mailchannels.EmailAddress(email="recipient@example.net")],
            ),
        ],
        subject="Newsletter",
        content=[
            mailchannels.Content(
                type="text/html",
                value=(
                    "<p>Hello!</p>"
                    f"<p><a href='{mailchannels.UNSUBSCRIBE_URL_PLACEHOLDER}'>"
                    "Unsubscribe</a></p>"
                ),
                template_type="mustache",
            ),
        ],
    )
)
```

**Always import the constant from `mailchannels`.** Do not hand-type the
placeholder string — typos are silent.

By itself, the in-body link is fine for occasional one-off sends. For
anything resembling bulk mail, combine it with the headers — see below.

## `List-Unsubscribe` Headers (Non-Transactional)

Setting `transactional: False` tells MailChannels to add
`List-Unsubscribe` and `List-Unsubscribe-Post` headers automatically.
These headers are what inbox providers read to render their own
"Unsubscribe" button next to the sender's name.

**Always include the in-body link in the same payload** so the message
is fully compliant on both surfaces:

```python
mailchannels.Emails.queue(
    mailchannels.EmailParams(
        from_=mailchannels.EmailAddress(email="sender@example.com"),
        personalizations=[
            mailchannels.Personalization(
                to=[mailchannels.EmailAddress(email="recipient@example.net")],
            ),
        ],
        subject="Marketing message",
        content=[
            mailchannels.Content(
                type="text/html",
                value=(
                    "<p>Today's update…</p>"
                    f"<p><a href='{mailchannels.UNSUBSCRIBE_URL_PLACEHOLDER}'>"
                    "Unsubscribe</a></p>"
                ),
                template_type="mustache",
            ),
        ],
        transactional=False,
        dkim_domain="example.com",
        dkim_selector="mcdkim",
    )
)
```

If `transactional: False` is set but the message has more than one
recipient per personalization, MailChannels returns **400 Bad Request**.

## When To Use Which

| Message type | In-body link | `transactional: False` headers |
| --- | --- | --- |
| Transactional (receipts, password resets, confirmations) | No | No (keep the default `True`). |
| Bulk / marketing / newsletter / notification | **Yes** | **Yes** — combine both in the same payload. |

There is essentially no situation where you'd want headers but not the
in-body link; if you're sending non-transactional mail, you need both.

Both modes require DKIM signing (see the intro). The example above shows
the minimum payload — `dkim_domain` + `dkim_selector`. See
[dkim](dkim.md) for how to create the underlying key.
