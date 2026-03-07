"""Self-update helper for MusicProd.

Detects whether the package was installed from a local git clone (editable
install) and pulls the latest changes from the remote, or falls back to
upgrading via pip.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


# URL used when falling back to a pip-based upgrade.
_REPO_URL = "https://github.com/AMix-hub/musicprod.git"

# Maximum number of parent directories to traverse when searching for .git.
_MAX_PARENT_TRAVERSAL = 10


def _find_git_root() -> Path | None:
    """Return the git repository root that contains this package, or None."""
    # Walk upward from the package source directory to find a .git directory.
    candidate = Path(__file__).resolve().parent
    for _ in range(_MAX_PARENT_TRAVERSAL):
        if (candidate / ".git").is_dir():
            return candidate
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent
    return None


def _run(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a subprocess and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def update_via_git(git_root: Path) -> str:
    """Pull the latest changes from the remote in *git_root*.

    Returns
    -------
    str
        A human-readable status message.

    Raises
    ------
    RuntimeError
        If the git pull command fails.
    """
    returncode, stdout, stderr = _run(["git", "pull", "--ff-only"], cwd=git_root)
    output = (stdout + stderr).strip()
    if returncode != 0:
        raise RuntimeError(f"git pull failed:\n{output}")
    return output or "Already up to date."


def update_via_pip() -> str:
    """Upgrade the *musicprod* package using pip.

    Returns
    -------
    str
        A human-readable status message.

    Raises
    ------
    RuntimeError
        If the pip upgrade command fails.
    """
    args = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        f"git+{_REPO_URL}",
    ]
    returncode, stdout, stderr = _run(args)
    output = (stdout + stderr).strip()
    if returncode != 0:
        raise RuntimeError(f"pip upgrade failed:\n{output}")
    return output or "Upgrade complete."


def self_update() -> tuple[str, str]:
    """Update MusicProd to the latest version on *main*.

    Tries a ``git pull`` first (works for editable/development installs).
    Falls back to ``pip install --upgrade git+<repo>`` otherwise.

    Returns
    -------
    tuple[str, str]
        ``(method, message)`` where *method* is ``"git"`` or ``"pip"``.

    Raises
    ------
    RuntimeError
        If the chosen update method fails.
    """
    git_root = _find_git_root()
    if git_root is not None:
        return "git", update_via_git(git_root)
    return "pip", update_via_pip()
