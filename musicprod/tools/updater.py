"""Self-update helper for MusicProd.

Detects whether the package was installed from a local git clone (editable
install) and pulls the latest changes from the remote, or falls back to
upgrading via pip.

When running as a frozen PyInstaller executable the updater instead checks
GitHub Releases for a newer ``musicprod-hub.exe``, downloads it, and
schedules a self-patch so the hub can restart into the new binary.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# URL used when falling back to a pip-based upgrade.
_REPO_URL = "https://github.com/AMix-hub/musicprod.git"

# Maximum number of parent directories to traverse when searching for .git.
_MAX_PARENT_TRAVERSAL = 10

# GitHub REST API endpoint for the latest release.
_GITHUB_RELEASES_API = (
    "https://api.github.com/repos/AMix-hub/musicprod/releases/latest"
)

# Name of the Windows executable asset attached to each release.
_EXE_ASSET_NAME = "musicprod-hub.exe"

# Path of the freshly downloaded exe set by update_via_exe(); read by the
# hub's restart handler so it can launch the new binary instead of the old one.
_pending_restart_exe: Path | None = None

# Trusted URL prefixes — download URLs must start with one of these.
_TRUSTED_URL_PREFIXES = (
    "https://github.com/",
    "https://objects.githubusercontent.com/",
)


# ---------------------------------------------------------------------------
# Version helpers
# ---------------------------------------------------------------------------


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse a semver string (optionally prefixed with ``v``) into an int tuple."""
    return tuple(int(x) for x in v.lstrip("v").split("."))


# ---------------------------------------------------------------------------
# Frozen-exe detection
# ---------------------------------------------------------------------------


def _is_frozen() -> bool:
    """Return ``True`` when running inside a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False))


# ---------------------------------------------------------------------------
# git / pip helpers (used for source / pip installs)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Exe-based self-patching update (used when running as a frozen exe)
# ---------------------------------------------------------------------------


def _http_get_json(url: str) -> dict:  # type: ignore[type-arg]
    """Fetch *url* and parse the response body as JSON.

    Only HTTPS URLs that start with a trusted prefix are allowed.
    """
    if not any(url.startswith(p) for p in _TRUSTED_URL_PREFIXES):
        raise ValueError(f"Untrusted URL rejected: {url!r}")
    req = urllib.request.Request(url, headers={"User-Agent": "musicprod-updater"})
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
        return json.loads(resp.read())  # type: ignore[return-value]


def _download_file(url: str, dest: Path) -> None:
    """Download *url* to *dest* in streaming chunks.

    Only HTTPS URLs that start with a trusted prefix are allowed.
    """
    if not any(url.startswith(p) for p in _TRUSTED_URL_PREFIXES):
        raise ValueError(f"Untrusted download URL rejected: {url!r}")
    req = urllib.request.Request(url, headers={"User-Agent": "musicprod-updater"})
    with urllib.request.urlopen(req, timeout=120) as resp, dest.open("wb") as fh:  # noqa: S310
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            fh.write(chunk)


def get_pending_restart_exe() -> Path | None:
    """Return the path of a freshly downloaded exe waiting to be applied.

    The hub's restart handler reads this to decide whether to launch the new
    binary or to simply re-run the current Python process.
    """
    return _pending_restart_exe


def update_via_exe() -> str:
    """Check GitHub Releases for a newer ``musicprod-hub.exe`` and download it.

    When a newer version is available the binary is downloaded to a temporary
    directory and ``_pending_restart_exe`` is set to its path.  The caller
    should then restart the hub so the new binary is launched.

    If the current version is already up to date ``_pending_restart_exe`` is
    left as ``None``.

    Returns
    -------
    str
        A human-readable status message.

    Raises
    ------
    RuntimeError
        If the GitHub API call fails, the asset is missing, or the download
        fails.
    """
    global _pending_restart_exe

    from musicprod import __version__

    release = _http_get_json(_GITHUB_RELEASES_API)
    latest_tag = release.get("tag_name", "")
    if not latest_tag:
        raise RuntimeError("GitHub release has no tag_name.")

    try:
        current = _parse_version(__version__)
        latest = _parse_version(latest_tag)
    except ValueError as exc:
        raise RuntimeError(f"Could not parse version numbers: {exc}") from exc

    if latest <= current:
        _pending_restart_exe = None
        return "Already up to date."

    # Locate the exe asset in the release.
    assets: list[dict] = release.get("assets", [])  # type: ignore[assignment]
    exe_asset = next(
        (a for a in assets if a.get("name", "") == _EXE_ASSET_NAME),
        None,
    )
    if exe_asset is None:
        raise RuntimeError(
            f"No '{_EXE_ASSET_NAME}' asset found in release {latest_tag}."
        )

    # Download to a temporary directory so we don't overwrite the running exe.
    tmp_dir = Path(tempfile.mkdtemp(prefix="musicprod_update_"))
    tmp_exe = tmp_dir / _EXE_ASSET_NAME
    _download_file(exe_asset["browser_download_url"], tmp_exe)

    _pending_restart_exe = tmp_exe
    version_str = latest_tag.lstrip("v")
    return f"Downloaded v{version_str} — click 'Restart Hub' to apply."


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def self_update() -> tuple[str, str]:
    """Update MusicProd to the latest version on *main*.

    Dispatch order:
    1. **Frozen exe** — download the latest ``musicprod-hub.exe`` from
       GitHub Releases (``update_via_exe``).
    2. **Git clone / editable install** — run ``git pull --ff-only``
       (``update_via_git``).
    3. **Regular pip install** — upgrade via
       ``pip install --upgrade git+<repo>`` (``update_via_pip``).

    Returns
    -------
    tuple[str, str]
        ``(method, message)`` where *method* is ``"exe"``, ``"git"``, or
        ``"pip"``.

    Raises
    ------
    RuntimeError
        If the chosen update method fails.
    """
    if _is_frozen():
        return "exe", update_via_exe()
    git_root = _find_git_root()
    if git_root is not None:
        return "git", update_via_git(git_root)
    return "pip", update_via_pip()
