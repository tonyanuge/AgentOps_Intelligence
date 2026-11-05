"""Inspect the AgentOps Intelligence repository foundation.

Owner: Tony Anuge
Deliverable: D01 - Repository foundation
"""

from pathlib import Path


def get_repository_root(path: Path) -> Path:
    """Validate and return the absolute repository directory."""

    # Convert the supplied path to an absolute path.
    root = path.expanduser().resolve()

    # Stop if the directory does not exist.
    if not root.is_dir():
        raise NotADirectoryError(f"Repository directory not found: {root}")

    return root


def inspect_foundation(root: Path) -> dict[str, bool]:
    """Check whether required configuration files exist."""

    # Files required or planned for the project foundation.
    expected_files = (
        ".python-version",
        ".gitignore",
        "pyproject.toml",
        "compose.yaml",
    )

    # Build a dictionary containing each file and its status.
    return {name: (root / name).is_file() for name in expected_files}


if __name__ == "__main__":
    # Find the repository root from this script's location.
    script_path = Path(__file__).resolve()
    project_path = script_path.parent.parent

    repository = get_repository_root(project_path)

    print(f"Repository root: {repository}")

    # Inspect the configuration files.
    results = inspect_foundation(repository)

    # Print the result for each file.
    for filename, exists in results.items():
        status = "FOUND" if exists else "MISSING"
        print(f"{filename}: {status}")
