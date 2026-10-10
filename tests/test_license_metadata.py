"""Verify installed package metadata exposes the redistributable MIT license."""
from importlib.metadata import metadata


def test_installed_license_metadata() -> None:
    """Require SPDX classification and included license without legacy ambiguity."""
    package = metadata("mailchannels")
    assert package["License-Expression"] == "MIT"
    assert "LICENSE" in (package.get_all("License-File") or [])
    assert package["License"] is None
    assert not any(
        classifier.startswith("License ::")
        for classifier in (package.get_all("Classifier") or [])
    )
