"""Tests for musicprod.tools.updater and the ``update`` CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from musicprod.cli import cli


# ---------------------------------------------------------------------------
# _find_git_root
# ---------------------------------------------------------------------------


def test_find_git_root_returns_path_when_git_dir_present(tmp_path):
    """_find_git_root should return the directory that contains .git."""
    from musicprod.tools.updater import _find_git_root

    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    # Simulate __file__ being inside a sub-package two levels deep.
    pkg = tmp_path / "musicprod" / "tools"
    pkg.mkdir(parents=True)
    fake_module = pkg / "updater.py"
    fake_module.touch()

    with patch("musicprod.tools.updater.__file__", str(fake_module)):
        result = _find_git_root()

    assert result == tmp_path


def test_find_git_root_returns_none_when_no_git_dir(tmp_path):
    """_find_git_root should return None when there is no .git directory."""
    from musicprod.tools.updater import _find_git_root

    # Point __file__ at an isolated directory with no .git ancestor.
    isolated = tmp_path / "isolated" / "pkg" / "tools"
    isolated.mkdir(parents=True)
    fake_module = isolated / "updater.py"
    fake_module.touch()

    with patch("musicprod.tools.updater.__file__", str(fake_module)):
        result = _find_git_root()

    assert result is None


# ---------------------------------------------------------------------------
# update_via_git
# ---------------------------------------------------------------------------


def test_update_via_git_success(tmp_path):
    """update_via_git returns the git output on success."""
    from musicprod.tools.updater import update_via_git

    with patch("musicprod.tools.updater._run") as mock_run:
        mock_run.return_value = (0, "Already up to date.\n", "")
        result = update_via_git(tmp_path)

    assert "Already up to date" in result
    mock_run.assert_called_once_with(["git", "pull", "--ff-only"], cwd=tmp_path)


def test_update_via_git_empty_output_returns_default_message(tmp_path):
    """update_via_git returns a sensible default when output is empty."""
    from musicprod.tools.updater import update_via_git

    with patch("musicprod.tools.updater._run") as mock_run:
        mock_run.return_value = (0, "", "")
        result = update_via_git(tmp_path)

    assert result == "Already up to date."


def test_update_via_git_failure_raises_runtime_error(tmp_path):
    """update_via_git raises RuntimeError when git returns non-zero."""
    from musicprod.tools.updater import update_via_git

    with patch("musicprod.tools.updater._run") as mock_run:
        mock_run.return_value = (1, "", "fatal: not a git repository")
        with pytest.raises(RuntimeError, match="git pull failed"):
            update_via_git(tmp_path)


# ---------------------------------------------------------------------------
# update_via_pip
# ---------------------------------------------------------------------------


def test_update_via_pip_success():
    """update_via_pip returns pip output on success."""
    from musicprod.tools.updater import update_via_pip

    with patch("musicprod.tools.updater._run") as mock_run:
        mock_run.return_value = (0, "Successfully installed musicprod-0.2.0\n", "")
        result = update_via_pip()

    assert "Successfully installed" in result


def test_update_via_pip_empty_output_returns_default_message():
    """update_via_pip returns a sensible default when output is empty."""
    from musicprod.tools.updater import update_via_pip

    with patch("musicprod.tools.updater._run") as mock_run:
        mock_run.return_value = (0, "", "")
        result = update_via_pip()

    assert result == "Upgrade complete."


def test_update_via_pip_failure_raises_runtime_error():
    """update_via_pip raises RuntimeError when pip returns non-zero."""
    from musicprod.tools.updater import update_via_pip

    with patch("musicprod.tools.updater._run") as mock_run:
        mock_run.return_value = (1, "", "ERROR: Could not find a version")
        with pytest.raises(RuntimeError, match="pip upgrade failed"):
            update_via_pip()


# ---------------------------------------------------------------------------
# self_update
# ---------------------------------------------------------------------------


def test_self_update_uses_git_when_git_root_found(tmp_path):
    """self_update should delegate to update_via_git when a git root exists."""
    from musicprod.tools import updater

    with patch.object(updater, "_find_git_root", return_value=tmp_path), \
         patch.object(updater, "update_via_git", return_value="Fast-forwarded.") as mock_git:
        method, msg = updater.self_update()

    assert method == "git"
    assert msg == "Fast-forwarded."
    mock_git.assert_called_once_with(tmp_path)


def test_self_update_falls_back_to_pip_when_no_git_root():
    """self_update should fall back to update_via_pip when no git root."""
    from musicprod.tools import updater

    with patch.object(updater, "_find_git_root", return_value=None), \
         patch.object(updater, "update_via_pip", return_value="Upgraded.") as mock_pip:
        method, msg = updater.self_update()

    assert method == "pip"
    assert msg == "Upgraded."
    mock_pip.assert_called_once()


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


def test_cli_update_command_success_git():
    """``musicprod update`` prints a success message for a git-based update."""
    runner = CliRunner()

    with patch("musicprod.tools.updater.self_update", return_value=("git", "Already up to date.")):
        result = runner.invoke(cli, ["update"])

    assert result.exit_code == 0
    assert "git pull" in result.output
    assert "Already up to date." in result.output
    assert "Restart" in result.output


def test_cli_update_command_success_pip():
    """``musicprod update`` prints a success message for a pip-based update."""
    runner = CliRunner()

    with patch("musicprod.tools.updater.self_update", return_value=("pip", "Upgrade complete.")):
        result = runner.invoke(cli, ["update"])

    assert result.exit_code == 0
    assert "pip upgrade" in result.output
    assert "Upgrade complete." in result.output
    assert "Restart" in result.output


def test_cli_update_command_failure():
    """``musicprod update`` exits with code 1 and shows an error on failure."""
    runner = CliRunner()

    with patch("musicprod.tools.updater.self_update", side_effect=RuntimeError("network error")):
        result = runner.invoke(cli, ["update"])

    assert result.exit_code == 1
    assert "Update failed" in result.output


def test_cli_update_command_success_exe():
    """``musicprod update`` shows 'exe download' label when running as frozen exe."""
    runner = CliRunner()

    with patch(
        "musicprod.tools.updater.self_update",
        return_value=("exe", "Downloaded v0.2.0 — click 'Restart Hub' to apply."),
    ):
        result = runner.invoke(cli, ["update"])

    assert result.exit_code == 0
    assert "exe download" in result.output
    assert "Restart" in result.output


# ---------------------------------------------------------------------------
# _parse_version
# ---------------------------------------------------------------------------


def test_parse_version_plain():
    from musicprod.tools.updater import _parse_version

    assert _parse_version("1.2.3") == (1, 2, 3)


def test_parse_version_with_v_prefix():
    from musicprod.tools.updater import _parse_version

    assert _parse_version("v0.1.0") == (0, 1, 0)


# ---------------------------------------------------------------------------
# _is_frozen
# ---------------------------------------------------------------------------


def test_is_frozen_false_in_tests():
    """_is_frozen should return False when running under pytest."""
    from musicprod.tools.updater import _is_frozen

    assert _is_frozen() is False


def test_is_frozen_true_when_frozen_attr_set():
    from musicprod.tools.updater import _is_frozen
    import sys

    with patch.object(sys, "frozen", True, create=True):
        assert _is_frozen() is True


# ---------------------------------------------------------------------------
# update_via_exe
# ---------------------------------------------------------------------------

_FAKE_RELEASE_NEWER = {
    "tag_name": "v0.2.0",
    "assets": [
        {
            "name": "musicprod-hub.exe",
            "browser_download_url": "https://example.com/musicprod-hub.exe",
        }
    ],
}

_FAKE_RELEASE_SAME = {
    "tag_name": "v0.1.0",
    "assets": [
        {
            "name": "musicprod-hub.exe",
            "browser_download_url": "https://example.com/musicprod-hub.exe",
        }
    ],
}


def test_update_via_exe_already_up_to_date(tmp_path):
    """update_via_exe returns 'Already up to date.' when release == current."""
    from musicprod.tools import updater

    with patch.object(updater, "_http_get_json", return_value=_FAKE_RELEASE_SAME):
        result = updater.update_via_exe()

    assert result == "Already up to date."
    assert updater.get_pending_restart_exe() is None


def test_update_via_exe_downloads_new_version(tmp_path):
    """update_via_exe downloads the exe and sets _pending_restart_exe."""
    from musicprod.tools import updater

    fake_exe = tmp_path / "musicprod-hub.exe"
    fake_exe.write_bytes(b"fake exe content")

    def fake_download(url: str, dest: Path) -> None:
        dest.write_bytes(b"fake exe content")

    with patch.object(updater, "_http_get_json", return_value=_FAKE_RELEASE_NEWER), \
         patch.object(updater, "_download_file", side_effect=fake_download), \
         patch("tempfile.mkdtemp", return_value=str(tmp_path)):
        result = updater.update_via_exe()

    assert "0.2.0" in result
    assert updater.get_pending_restart_exe() is not None
    assert updater.get_pending_restart_exe().name == "musicprod-hub.exe"  # type: ignore[union-attr]


def test_update_via_exe_missing_asset_raises():
    """update_via_exe raises RuntimeError when no exe asset is in the release."""
    from musicprod.tools import updater

    release_no_asset = {"tag_name": "v0.2.0", "assets": []}

    with patch.object(updater, "_http_get_json", return_value=release_no_asset):
        with pytest.raises(RuntimeError, match="No 'musicprod-hub.exe' asset"):
            updater.update_via_exe()


def test_update_via_exe_missing_tag_raises():
    """update_via_exe raises RuntimeError when the release has no tag_name."""
    from musicprod.tools import updater

    with patch.object(updater, "_http_get_json", return_value={"assets": []}):
        with pytest.raises(RuntimeError, match="no tag_name"):
            updater.update_via_exe()


def test_http_get_json_rejects_untrusted_url():
    """_http_get_json raises ValueError for non-GitHub URLs."""
    from musicprod.tools.updater import _http_get_json

    with pytest.raises(ValueError, match="Untrusted URL"):
        _http_get_json("http://evil.example.com/release")


def test_http_get_json_accepts_github_api_url():
    """_http_get_json accepts https://api.github.com/ URLs (does not raise ValueError)."""
    from musicprod.tools.updater import _http_get_json

    fake_response = b'{"tag_name": "v0.2.0", "assets": []}'
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.read.return_value = fake_response

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = _http_get_json(
            "https://api.github.com/repos/AMix-hub/musicprod/releases/latest"
        )

    assert result["tag_name"] == "v0.2.0"


def test_download_file_rejects_untrusted_url(tmp_path):
    """_download_file raises ValueError for non-GitHub URLs."""
    from musicprod.tools.updater import _download_file

    with pytest.raises(ValueError, match="Untrusted download URL"):
        _download_file("http://evil.example.com/musicprod-hub.exe", tmp_path / "f.exe")


# ---------------------------------------------------------------------------
# self_update dispatching
# ---------------------------------------------------------------------------


def test_self_update_uses_exe_when_frozen(tmp_path):
    """self_update dispatches to update_via_exe when sys.frozen is set."""
    from musicprod.tools import updater
    import sys

    with patch.object(sys, "frozen", True, create=True), \
         patch.object(updater, "update_via_exe", return_value="Already up to date.") as mock_exe:
        method, msg = updater.self_update()

    assert method == "exe"
    assert msg == "Already up to date."
    mock_exe.assert_called_once()

