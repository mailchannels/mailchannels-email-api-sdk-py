"""Domain-check resource exports."""

from .check_domain import CheckDomain, CheckDomainResource
from .types import (
    CheckDomainParams,
    CheckDomainResult,
    CheckResults,
    DkimResult,
    DkimSetting,
    DomainCheckVerdict,
    LockdownResult,
    SenderDomainResult,
    SpfResult,
)

__all__ = [
    "CheckDomain",
    "CheckDomainParams",
    "CheckDomainResource",
    "CheckDomainResult",
    "CheckResults",
    "DkimResult",
    "DkimSetting",
    "DomainCheckVerdict",
    "LockdownResult",
    "SenderDomainResult",
    "SpfResult",
]
