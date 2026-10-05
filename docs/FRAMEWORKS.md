# Django and FastAPI recipes

These recipes use the official [`mailchannels` package](https://pypi.org/project/mailchannels/)
directly. Complete the [Python quickstart](https://docs.mailchannels.com/email-api/python/quickstart)
and configure your sender domain first. Keep `MAILCHANNELS_API_KEY` in your
deployment's secret store. A dry run validates a request without sending email;
it does not prove inbox delivery. The free plan allows 100 emails per day and
restricts recipients to verified account users until a payment method is added.

## Django: a synchronous application service

In an existing Django project, install the SDK with `uv add mailchannels`.
Add custom settings to your project's `settings.py`:

```python
import os

MAILCHANNELS_API_KEY = os.environ["MAILCHANNELS_API_KEY"]
MAILCHANNELS_SENDER = os.environ["MAILCHANNELS_SENDER"]
```

Create an application service such as `your_app/email_service.py`:

```python
from django.conf import settings
import mailchannels


def send_notification(recipient: str, *, dry_run: bool = True) -> None:
    """Validate or send a notification to an application-approved recipient."""
    with mailchannels.Client(api_key=settings.MAILCHANNELS_API_KEY) as client:
        client.emails.send(
            {
                "from": {"email": settings.MAILCHANNELS_SENDER},
                "to": [{"email": recipient}],
                "subject": "Your notification",
                "text": "Your requested operation has completed.",
            },
            dry_run=dry_run,
        )
```

Call this service from your synchronous application code or task worker. The
default validates only; pass `dry_run=False` deliberately when ready to send.
Use a recipient selected and authorized by your application. SDK exceptions
propagate to the caller so your existing error handling can record a failure.
The context manager closes the synchronous HTTP session after the call.

This service does not configure Django's `EMAIL_BACKEND`, implement
`django.core.mail.send_mail`, or add an Anymail provider. For an async Django
view, use `async with mailchannels.Client(...)` and
`await client.emails.send_async(...)` instead of blocking the event loop with
the synchronous service above. See Django's [settings](https://docs.djangoproject.com/en/5.2/topics/settings/)
and [async support](https://docs.djangoproject.com/en/5.2/topics/async/) documentation.

## FastAPI: an async client owned by the application

In an existing FastAPI project, install the async extra:

```bash
uv add "mailchannels[async]"
```

Use FastAPI's [lifespan](https://fastapi.tiangolo.com/advanced/events/) to create
one client per application process and close it on shutdown:

```python
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
import mailchannels


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Own the async MailChannels client for this application process."""
    async with mailchannels.Client(
        api_key=os.environ["MAILCHANNELS_API_KEY"]
    ) as client:
        app.state.mailchannels = client
        yield


app = FastAPI(lifespan=lifespan)


async def send_notification(
    request: Request, recipient: str, *, dry_run: bool = True
) -> None:
    """Validate or send a notification from an authorized application flow."""
    await request.app.state.mailchannels.emails.send_async(
        {
            "from": {"email": os.environ["MAILCHANNELS_SENDER"]},
            "to": [{"email": recipient}],
            "subject": "Your notification",
            "text": "Your requested operation has completed.",
        },
        dry_run=dry_run,
    )
```

Call the helper from an existing authenticated route after checking that the
user may trigger the notification. Keep the sender and dry-run choice under
application control. If your app already has a lifespan handler, incorporate
this client into that handler rather than replacing its other startup work.

`send_async` uses nonblocking Python HTTP to call `/send`; it does not select
the API's `/send-async` queue. Use `queue_async` for that separate behavior,
which has no dry-run option. For retries and delivery tracking, consult
[Advanced Usage](ADVANCED.md) before adding automatic resend logic.
