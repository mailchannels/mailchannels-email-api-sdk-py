"""Regenerate the README block that declares the targeted Email API version.

The README is user documentation, but one line — the "Built and tested against
MailChannels Email API X.Y.Z." statement — is derived from
`mailchannels.API_SPEC_COMPATIBILITY` and must stay in sync with the OpenAPI
spec that ships with the SDK. This script rewrites the block between the
generated-block markers in README.md and exits non-zero when run with
`--check` if the file is stale.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

from mailchannels.compatibility import API_SPEC_COMPATIBILITY

logger = logging.getLogger(__name__)

DEFAULT_README = Path("README.md")
START_MARKER = "<!-- generated:api-version -->"
END_MARKER = "<!-- /generated:api-version -->"
_BLOCK_RE = re.compile(
    rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
    re.DOTALL,
)


def render_block() -> str:
    """Return the generated README block contents."""
    version = API_SPEC_COMPATIBILITY.openapi_version
    return (
        f"{START_MARKER}\n"
        f"Built and tested against MailChannels Email API {version}.\n"
        f"{END_MARKER}"
    )


def regenerate(text: str) -> str:
    """Return the README text with the generated block refreshed."""
    if START_MARKER not in text or END_MARKER not in text:
        raise ValueError(
            "README is missing the generated:api-version block; "
            f"add `{START_MARKER}` and `{END_MARKER}` markers."
        )
    return _BLOCK_RE.sub(render_block(), text, count=1)


def main() -> int:
    """Run the README version-line regenerator."""
    args = _parser().parse_args()
    readme_path: Path = args.readme
    original = readme_path.read_text(encoding="utf-8")
    refreshed = regenerate(original)
    if args.check:
        if original != refreshed:
            print(
                f"README.md is out of date with API_SPEC_COMPATIBILITY "
                f"({API_SPEC_COMPATIBILITY.openapi_version}). "
                "Run `scripts/regen_readme_version.py` and commit the result.",
                file=sys.stderr,
            )
            return 1
        print("README.md API version line is up to date.")
        return 0
    if original == refreshed:
        print("README.md API version line is up to date.")
        return 0
    readme_path.write_text(refreshed, encoding="utf-8")
    version = API_SPEC_COMPATIBILITY.openapi_version
    print(f"Updated README.md API version line to {version}.")
    return 0


def _parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--readme",
        type=Path,
        default=DEFAULT_README,
        help="Path to the README file (default: README.md).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if README is out of sync, instead of rewriting it.",
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
