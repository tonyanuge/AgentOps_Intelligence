"""Tests for the AgentOps foundation audit.

Owner: Platform Engineering
Deliverable: D01 - Repository foundation
"""

from pathlib import Path

import pytest

from scripts.foundation_audit import (
    get_repository_root,
    inspect_foundation,
)


def test_get_repository_root(tmp_path: Path) -> None:
    """Verify that a valid directory is accepted."""

    # Check the root against its resolved path.
    result = get_repository_root(tmp_path)

    assert result == tmp_path.resolve()


def test_get_repository_root_invalid(tmp_path: Path) -> None:
    """Verify that a missing directory is rejected."""

    # Create a path without creating the directory.
    missing_path = tmp_path / "missing"

    # The function must raise the expected exception.
    with pytest.raises(NotADirectoryError):
        get_repository_root(missing_path)


def test_inspect_foundation(tmp_path: Path) -> None:
    """Verify detection of existing and missing files."""

    # Create two configuration files in a temporary directory.
    (tmp_path / ".python-version").touch()
    (tmp_path / ".gitignore").touch()

    # Run the audit against the temporary directory.
    results = inspect_foundation(tmp_path)

    # Confirm the complete expected result.
    assert results == {
        ".python-version": True,
        ".gitignore": True,
        "pyproject.toml": False,
        "compose.yaml": False,
    }
