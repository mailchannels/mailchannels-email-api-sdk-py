# Django and FastAPI recipes

These recipes use the official [`mailchannels` package](https://pypi.org/project/mailchannels/)
directly. Complete the [Python quickstart](https://docs.mailchannels.com/email-api/python/quickstart)
and configure your sender domain first. Keep `MAILCHANNELS_API_KEY` in your
deployment's secret store. A dry run validates a request without sending email;
it does not prove inbox delivery. The [free plan](https://docs.mailchannels.com/email-api/billing/pricing) allows 100 emails per day and
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
    payload: mailchannels.SendParams = {
        "from_": {"email": settings.MAILCHANNELS_SENDER},
        "to": recipient,
        "subject": "Your notification",
        "text": "Your requested operation has completed.",
    }
    with mailchannels.Client(api_key=settings.MAILCHANNELS_API_KEY) as client:
        client.emails.send(payload, dry_run=dry_run)
```

Call this service from your synchronous application code or task worker. The
default validates only; pass `dry_run=False` deliberately when ready to send.
Use a recipient selected and authorized by your application. SDK exceptions
propagate to the caller so your existing error handling can record a failure.
The context manager closes the synchronous HTTP session after the call.
Use the SDK's typed `from_` key; it is serialized to the API's `from` field.

This service does not configure Django's `EMAIL_BACKEND`, implement
`django.core.mail.send_mail`, or add an Anymail provider. For an async Django
view, first install the async extra with `uv add "mailchannels[async]"`, then
use `async with mailchannels.Client(...)` and
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
from typing import AsyncIterator, Literal, cast

from fastapi import FastAPI, Request
import mailchannels


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Own the async MailChannels client for this application process."""
    client = mailchannels.Client[Literal[False]](
        api_key=os.environ["MAILCHANNELS_API_KEY"]
    )
    async with client:
        app.state.mailchannels = client
        yield


app = FastAPI(lifespan=lifespan)


async def send_notification(
    request: Request, recipient: str, *, dry_run: bool = True
) -> None:
    """Validate or send a notification from an authorized application flow."""
    client = cast(mailchannels.Client[Literal[False]], request.app.state.mailchannels)
    payload: mailchannels.SendParams = {
        "from_": {"email": os.environ["MAILCHANNELS_SENDER"]},
        "to": recipient,
        "subject": "Your notification",
        "text": "Your requested operation has completed.",
    }
    await client.emails.send_async(payload, dry_run=dry_run)
```

The cast gives the dynamically stored application client its SDK type so the
send call and payload are checked. It relies on this lifespan handler owning
`app.state.mailchannels`; a cast is not runtime validation. Keep that state slot
private to this handler and do not replace it with another value.

Call the helper from an existing authenticated route after checking that the
user may trigger the notification. Keep the sender and dry-run choice under
application control. If your app already has a lifespan handler, incorporate
this client into that handler rather than replacing its other startup work.

`send_async` uses nonblocking Python HTTP to call `/send`; it does not select
the API's `/send-async` queue. Use `queue_async` for that separate behavior,
which has no dry-run option. For retries and delivery tracking, consult
[Advanced Usage](ADVANCED.md) before adding automatic resend logic.
