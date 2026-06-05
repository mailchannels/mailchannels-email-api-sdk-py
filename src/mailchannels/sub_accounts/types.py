"""Sub-account request and response types."""

from __future__ import annotations

from typing import Any, TypedDict

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import NotRequired

from ..exceptions import MailChannelsError
from ..usage.types import UsageStats as UsageStats  # noqa: F401  (re-exported)


class CreateSubAccountParams(TypedDict, total=False):
    """Parameters for creating a MailChannels sub-account."""

    company_name: NotRequired[str]
    handle: NotRequired[str]


class SetLimitParams(TypedDict):
    """Parameters for setting a sub-account sending limit."""

    sends: int


class SubAccount(BaseModel):
    """MailChannels sub-account response model."""

    model_config = ConfigDict(extra="allow")

    handle: str
    company_name: str | None = None
    enabled: bool


class SubAccountLimit(BaseModel):
    """MailChannels sub-account sending limit response model."""

    model_config = ConfigDict(extra="allow")

    sends: int | None = None
    monthly_limit: int | None = None


class ApiKey(BaseModel):
    """MailChannels sub-account API key response model."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    key: str | None = None


class SmtpPassword(BaseModel):
    """MailChannels sub-account SMTP password response model."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    enabled: bool | None = None
    smtp_password: str | None = None


class SubAccountList(BaseModel):
    """Paged list of sub-accounts returned from `/sub-account`."""

    model_config = ConfigDict(extra="allow")

    data: list[SubAccount] = Field(default_factory=list)
    http_headers: dict[str, str] = Field(default_factory=dict)


class ApiKeyList(BaseModel):
    """Paged list of API keys for a sub-account."""

    model_config = ConfigDict(extra="allow")

    data: list[ApiKey] = Field(default_factory=list)
    http_headers: dict[str, str] = Field(default_factory=dict)


class SmtpPasswordList(BaseModel):
    """Paged list of SMTP passwords for a sub-account."""

    model_config = ConfigDict(extra="allow")

    data: list[SmtpPassword] = Field(default_factory=list)
    http_headers: dict[str, str] = Field(default_factory=dict)


def compact_payload(values: dict[str, Any]) -> dict[str, Any]:
    """Remove unset values from a request payload."""
    return {key: value for key, value in values.items() if value is not None}


def limit_payload(
    *,
    sends: int | None = None,
    monthly_limit: int | None = None,
) -> dict[str, int]:
    """Build the documented sub-account limit payload."""
    if sends is not None and monthly_limit is not None:
        raise MailChannelsError(
            "Pass either `sends` or `monthly_limit`, not both.",
            code="InvalidLimitParameters",
        )
    if sends is None and monthly_limit is None:
        raise MailChannelsError(
            "Pass `sends` to set a sub-account limit.",
            code="MissingLimitParameter",
        )
    limit = sends if sends is not None else monthly_limit
    if limit is None:
        raise MailChannelsError(
            "Pass `sends` to set a sub-account limit.",
            code="MissingLimitParameter",
        )
    return {"sends": limit}
