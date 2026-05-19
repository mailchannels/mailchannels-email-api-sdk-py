"""Tests for the README API-version drift guard."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import mailchannels

ROOT = Path(__file__).resolve().parents[1]


def _load_regen_script() -> ModuleType:
    """Load the README version regeneration script as a test module."""
    path = ROOT / "scripts" / "regen_readme_version.py"
    spec = importlib.util.spec_from_file_location("regen_readme_version", path)
    if spec is None or spec.loader is None:
        raise ImportError("Could not load README regeneration script.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


regen = _load_regen_script()


def test_readme_records_targeted_email_api_version() -> None:
    """The README declares the Email API version the SDK was built against."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert regen.START_MARKER in readme
    assert regen.END_MARKER in readme
    expected_line = (
        "Built and tested against MailChannels Email API "
        f"{mailchannels.API_SPEC_COMPATIBILITY.openapi_version}."
    )
    assert expected_line in readme


def test_readme_version_block_matches_regenerator_output() -> None:
    """`regen_readme_version.py --check` would pass on the committed README."""
    readme_path = ROOT / "README.md"
    original = readme_path.read_text(encoding="utf-8")

    refreshed = regen.regenerate(original)

    assert original == refreshed, (
        "README.md is out of sync with API_SPEC_COMPATIBILITY. "
        "Run scripts/regen_readme_version.py and commit the result."
    )
