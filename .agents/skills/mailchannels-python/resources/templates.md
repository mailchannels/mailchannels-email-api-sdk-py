# Templates

MailChannels templates are **send-payload fields**, not a template CRUD
resource. There is no "create template" endpoint. To use a template:

1. Set `template_type: "mustache"` on each templated content item.
2. Provide variables in `dynamic_template_data` on each personalization.

The only supported `template_type` is `mustache`.

## Single Recipient

```python
import mailchannels

mailchannels.Emails.send(
    mailchannels.EmailParams(
        from_=mailchannels.EmailAddress(email="sender@example.com"),
        personalizations=[
            mailchannels.Personalization(
                to=[mailchannels.EmailAddress(email="jane@example.net")],
                dynamic_template_data={"name": "Jane"},
            ),
        ],
        subject="Hello {{name}}",
        content=[
            mailchannels.Content(
                type="text/plain",
                value="Hello {{name}}",
                template_type="mustache",
            ),
            mailchannels.Content(
                type="text/html",
                value="<p>Hello {{name}}</p>",
                template_type="mustache",
            ),
        ],
    )
)
```

## Multiple Recipients With Per-Recipient Variables

Each personalization renders independently with its own variables:

```python
mailchannels.Emails.queue(
    mailchannels.EmailParams(
        from_=mailchannels.EmailAddress(email="sender@example.com"),
        personalizations=[
            mailchannels.Personalization(
                to=[mailchannels.EmailAddress(email="jane@example.net")],
                dynamic_template_data={"name": "Jane", "plan": "Pro"},
            ),
            mailchannels.Personalization(
                to=[mailchannels.EmailAddress(email="alex@example.net")],
                dynamic_template_data={"name": "Alex", "plan": "Free"},
            ),
        ],
        subject="Hi {{name}}",
        content=[
            mailchannels.Content(
                type="text/plain",
                value="Hi {{name}}, you're on the {{plan}} plan.",
                template_type="mustache",
            ),
        ],
    )
)
```

## Allowed `dynamic_template_data` Value Types

Keys are strings. Values may be:

- string
- boolean
- number
- list of any of the above
- map with string keys and values of any of the above (nested)

## Preview Without Sending

Use `dry_run=True` on `Emails.send()` to render and validate without delivering:

```python
preview = mailchannels.Emails.send(message, dry_run=True)
# preview.data is the list of rendered messages, one per personalization.
```

Dry-run is the right way to confirm that a template renders correctly before
shipping a new template into production.

## Subject Templates

The top-level `subject` field is **also** mustache-rendered when content has
`template_type: "mustache"`. There is no separate subject template type.
