"""Tests for musicprod.tools.metadata_editor."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, call


def _make_mock_audio(tags: dict | None = None):
    mock = MagicMock()
    if tags is not None:
        mock.tags = {k: [v] for k, v in tags.items()}
    else:
        mock.tags = None
    return mock


# ---------------------------------------------------------------------------
# read_metadata
# ---------------------------------------------------------------------------

def test_read_file_not_found():
    from musicprod.tools.metadata_editor import read_metadata

    with pytest.raises(FileNotFoundError, match="not found"):
        read_metadata("/non/existent/file.mp3")


def test_read_returns_dict(tmp_path):
    from musicprod.tools.metadata_editor import read_metadata

    dummy = tmp_path / "track.mp3"
    dummy.write_bytes(b"\x00" * 64)

    mock_audio = _make_mock_audio({"title": "Cool Song", "artist": "DJ X"})
    with patch("mutagen.File", return_value=mock_audio):
        result = read_metadata(str(dummy))

    assert result["title"] == "Cool Song"
    assert result["artist"] == "DJ X"


def test_read_empty_tags_returns_empty_dict(tmp_path):
    from musicprod.tools.metadata_editor import read_metadata

    dummy = tmp_path / "track.mp3"
    dummy.write_bytes(b"\x00" * 64)

    mock_audio = _make_mock_audio({})
    with patch("mutagen.File", return_value=mock_audio):
        result = read_metadata(str(dummy))

    assert result == {}


def test_read_none_tags_returns_empty_dict(tmp_path):
    from musicprod.tools.metadata_editor import read_metadata

    dummy = tmp_path / "track.mp3"
    dummy.write_bytes(b"\x00" * 64)

    mock_audio = _make_mock_audio(None)
    with patch("mutagen.File", return_value=mock_audio):
        result = read_metadata(str(dummy))

    assert result == {}


def test_read_mutagen_returns_none_raises(tmp_path):
    from musicprod.tools.metadata_editor import read_metadata

    dummy = tmp_path / "track.mp3"
    dummy.write_bytes(b"\x00" * 64)

    with patch("mutagen.File", return_value=None):
        with pytest.raises(RuntimeError, match="Unsupported or unreadable"):
            read_metadata(str(dummy))


# ---------------------------------------------------------------------------
# write_metadata
# ---------------------------------------------------------------------------

def test_write_file_not_found():
    from musicprod.tools.metadata_editor import write_metadata

    with pytest.raises(FileNotFoundError, match="not found"):
        write_metadata("/non/existent/file.mp3", title="X")


def test_write_sets_tags_and_saves(tmp_path):
    from musicprod.tools.metadata_editor import write_metadata

    dummy = tmp_path / "track.mp3"
    dummy.write_bytes(b"\x00" * 64)

    mock_audio = _make_mock_audio({})
    with patch("mutagen.File", return_value=mock_audio) as mock_file:
        write_metadata(str(dummy), title="New Title", artist="New Artist")

    mock_audio.save.assert_called_once()
    assert mock_audio.tags["title"] == ["New Title"]
    assert mock_audio.tags["artist"] == ["New Artist"]


def test_write_none_tags_adds_tags(tmp_path):
    """If the file has no tags, add_tags() should be called and tags populated."""
    from musicprod.tools.metadata_editor import write_metadata

    dummy = tmp_path / "track.mp3"
    dummy.write_bytes(b"\x00" * 64)

    mock_audio = _make_mock_audio(None)

    def _add_tags():
        # Simulate mutagen setting audio.tags after add_tags() is called.
        mock_audio.tags = {}

    mock_audio.add_tags.side_effect = _add_tags

    with patch("mutagen.File", return_value=mock_audio):
        write_metadata(str(dummy), title="Hello")

    mock_audio.add_tags.assert_called_once()
    assert mock_audio.tags.get("title") == ["Hello"]
