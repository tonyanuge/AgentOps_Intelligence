"""Check file paths against repository publication rules.

Owner: Tony Anuge
Deliverable: D01 - Repository publication safeguards
"""

import os
import subprocess
import sys
from pathlib import Path

# Directory names that must not be published.
BLOCKED_DIRECTORIES = {
    ".aws",
    ".venv",
    "__pycache__",
    "learning-only",
    "personal-notes",
    "private",
    "scratch",
}

# File extensions that may contain sensitive information.
BLOCKED_SUFFIXES = (
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".tfstate",
    ".tfvars",
    ".tfvars.json",
    ".tfplan",
)


def is_prohibited_path(file_path: str) -> bool:
    """Return True when a path violates publication rules."""

    # Git uses forward slashes. Normalise Windows paths too.
    normalised = file_path.replace("\\", "/").lower()

    # Separate directories from the filename.
    parts = normalised.split("/")
    filename = parts[-1]

    # Reject private directories at any level.
    if any(part in BLOCKED_DIRECTORIES for part in parts[:-1]):
        return True

    # Reject local environment files, but permit a template.
    if filename == ".env":
        return True

    if filename.startswith(".env.") and filename != ".env.example":
        return True

    # Reject sensitive files, including Terraform state backups.
    return filename.endswith(BLOCKED_SUFFIXES) or ".tfstate." in filename


def get_index_paths(repo_root: Path) -> list[str]:
    """Return file paths recorded in the Git index."""

    # Read tracked and staged paths without changing Git.
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--full-name", "-z"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )

    # Git separates paths with null bytes when -z is used.
    # Decode each path using the operating system encoding.
    return [os.fsdecode(path) for path in result.stdout.split(b"\0") if path]


def check_index_paths(repo_root: Path) -> list[str]:
    """Return prohibited paths found in the Git index."""

    # Read files already tracked or staged in Git.
    paths = get_index_paths(repo_root)

    # Identify files that violate publication rules.
    return [path for path in paths if is_prohibited_path(path)]


def main(repo_root: Path) -> int:
    """Check repository publication rules and return an exit code."""

    # Do not report success if Git inspection fails.
    try:
        violations = check_index_paths(repo_root)

    except (OSError, subprocess.CalledProcessError):
        print(
            "ERROR: Unable to inspect the Git index.",
            file=sys.stderr,
        )
        return 2

    # Report prohibited paths without reading file contents.
    if violations:
        print(
            "BLOCKED: Prohibited files found:",
            file=sys.stderr,
        )

        for path in violations:
            print(f"  {path}", file=sys.stderr)

        return 1

    # No publication violations were detected.
    print("PASS: No prohibited files found in the Git index.")
    return 0


if __name__ == "__main__":
    # Resolve the project root relative to this script.
    project_root = Path(__file__).resolve().parent.parent

    # Return the appropriate exit code to the terminal or CI.
    raise SystemExit(main(project_root))
