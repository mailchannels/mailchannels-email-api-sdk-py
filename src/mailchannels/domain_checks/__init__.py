"""Domain-check resource exports."""

from .domain_checks import (
    CheckDomain,
    CheckDomainResource,
    DomainChecks,
    DomainChecksResource,
)
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
    "CheckDomainParams",
    "CheckDomain",
    "CheckDomainResult",
    "CheckDomainResource",
    "CheckResults",
    "DkimResult",
    "DkimSetting",
    "DomainCheckVerdict",
    "DomainChecks",
    "DomainChecksResource",
    "LockdownResult",
    "SenderDomainResult",
    "SpfResult",
]
