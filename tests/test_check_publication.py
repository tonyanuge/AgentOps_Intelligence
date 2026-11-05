"""Unit tests for repository publication rules.

Owner: Tony Anuge
Deliverable: D01
"""

from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess
from unittest.mock import patch

import pytest

from scripts.check_publication import (
    check_index_paths,
    get_index_paths,
    is_prohibited_path,
    main,
)


@pytest.mark.parametrize(
    "file_path",
    [
        ".env",
        ".env.local",
        ".aws/credentials",
        "private/notes.txt",
        "scratch/experiment.py",
        "learning-only/example.py",
        "config/secret.pem",
        "config\\secret.key",
        "terraform/production.tfvars",
        "infra/terraform.tfstate.backup",
        "infra/production.tfvars.json",
        "infra/changes.tfplan",
    ],
)
def test_prohibited_paths(file_path: str) -> None:
    """Verify that prohibited paths are rejected."""
    assert is_prohibited_path(file_path) is True


@pytest.mark.parametrize(
    "file_path",
    [
        "pyproject.toml",
        "uv.lock",
        ".env.example",
        "scripts/foundation_audit.py",
        "tests/fixtures/sample.json",
        "benchmark/seal/split.json",
    ],
)
def test_approved_paths(file_path: str) -> None:
    """Verify that legitimate project paths are accepted."""
    assert is_prohibited_path(file_path) is False


def test_get_index_paths(tmp_path: Path) -> None:
    """Verify that Git index paths are read correctly."""

    # Simulate Git output without changing the real repository.
    fake_result = CompletedProcess(
        args=["git", "ls-files"],
        returncode=0,
        stdout=b"scripts/app.py\0.env\0notes/my notes.txt\0",
        stderr=b"",
    )

    # Replace the Git command with controlled test output.
    with patch(
        "scripts.check_publication.subprocess.run",
        return_value=fake_result,
    ) as mock_run:
        paths = get_index_paths(tmp_path)

    # Check that the paths were decoded correctly.
    assert paths == [
        "scripts/app.py",
        ".env",
        "notes/my notes.txt",
    ]

    # Verify that the expected read-only command was used.
    mock_run.assert_called_once_with(
        ["git", "ls-files", "--cached", "--full-name", "-z"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )


def test_check_index_paths_finds_violations(tmp_path: Path) -> None:
    """Verify that prohibited Git-index paths are detected."""

    paths = [
        "scripts/app.py",
        ".env",
        "private/notes.txt",
        "tests/test_app.py",
    ]

    with patch(
        "scripts.check_publication.get_index_paths",
        return_value=paths,
    ):
        violations = check_index_paths(tmp_path)

    assert violations == [
        ".env",
        "private/notes.txt",
    ]


def test_check_index_paths_allows_safe_files(tmp_path: Path) -> None:
    """Verify that approved project files pass."""

    paths = [
        "pyproject.toml",
        ".env.example",
        "tests/test_app.py",
    ]

    with patch(
        "scripts.check_publication.get_index_paths",
        return_value=paths,
    ):
        violations = check_index_paths(tmp_path)

    assert violations == []


def test_main_passes_for_safe_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify that a safe Git index produces exit code zero."""

    with patch(
        "scripts.check_publication.check_index_paths",
        return_value=[],
    ):
        exit_code = main(tmp_path)

    assert exit_code == 0
    assert "PASS" in capsys.readouterr().out


def test_main_blocks_prohibited_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify that prohibited paths produce exit code one."""

    with patch(
        "scripts.check_publication.check_index_paths",
        return_value=[".env", "private/notes.txt"],
    ):
        exit_code = main(tmp_path)

    output = capsys.readouterr()

    assert exit_code == 1
    assert ".env" in output.err
    assert "private/notes.txt" in output.err


def test_main_fails_when_git_inspection_fails(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify that a Git error cannot produce a successful result."""

    git_error = CalledProcessError(
        returncode=128,
        cmd=["git", "ls-files"],
    )

    with patch(
        "scripts.check_publication.check_index_paths",
        side_effect=git_error,
    ):
        exit_code = main(tmp_path)

    assert exit_code == 2
    assert "ERROR" in capsys.readouterr().err
