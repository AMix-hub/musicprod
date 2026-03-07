"""Tests for musicprod.tools.youtube_to_mp3."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path


def test_empty_url_raises_value_error():
    from musicprod.tools.youtube_to_mp3 import download_youtube_to_mp3

    with pytest.raises(ValueError, match="empty"):
        download_youtube_to_mp3("")


def test_non_youtube_url_raises_value_error():
    from musicprod.tools.youtube_to_mp3 import download_youtube_to_mp3

    with pytest.raises(ValueError, match="YouTube"):
        download_youtube_to_mp3("https://vimeo.com/123456")


def test_whitespace_only_url_raises_value_error():
    from musicprod.tools.youtube_to_mp3 import download_youtube_to_mp3

    with pytest.raises(ValueError, match="empty"):
        download_youtube_to_mp3("   ")


@patch("musicprod.tools.youtube_to_mp3.yt_dlp.YoutubeDL")
def test_successful_download_default_output(mock_ydl_cls, tmp_path, monkeypatch):
    """A successful download returns a Path ending in .mp3."""
    from musicprod.tools.youtube_to_mp3 import download_youtube_to_mp3

    monkeypatch.chdir(tmp_path)

    fake_info = {"title": "My Cool Song"}
    mock_ydl = MagicMock()
    mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
    mock_ydl.__exit__ = MagicMock(return_value=False)
    mock_ydl.extract_info.return_value = fake_info
    mock_ydl_cls.return_value = mock_ydl

    result = download_youtube_to_mp3("https://www.youtube.com/watch?v=abc123")

    assert result.suffix == ".mp3"
    assert result.name == "My Cool Song.mp3"


@patch("musicprod.tools.youtube_to_mp3.yt_dlp.YoutubeDL")
def test_successful_download_custom_output(mock_ydl_cls, tmp_path):
    """When output_path is given, the returned Path matches it."""
    from musicprod.tools.youtube_to_mp3 import download_youtube_to_mp3

    fake_info = {"title": "Whatever"}
    mock_ydl = MagicMock()
    mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
    mock_ydl.__exit__ = MagicMock(return_value=False)
    mock_ydl.extract_info.return_value = fake_info
    mock_ydl_cls.return_value = mock_ydl

    out = str(tmp_path / "output.mp3")
    result = download_youtube_to_mp3(
        "https://www.youtube.com/watch?v=abc123", output_path=out
    )

    assert result == Path(out).resolve()


@patch("musicprod.tools.youtube_to_mp3.yt_dlp.YoutubeDL")
def test_download_error_raises_runtime_error(mock_ydl_cls):
    """A DownloadError from yt-dlp is re-raised as RuntimeError."""
    import yt_dlp
    from musicprod.tools.youtube_to_mp3 import download_youtube_to_mp3

    mock_ydl = MagicMock()
    mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
    mock_ydl.__exit__ = MagicMock(return_value=False)
    mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError("network error")
    mock_ydl_cls.return_value = mock_ydl

    with pytest.raises(RuntimeError, match="yt-dlp download failed"):
        download_youtube_to_mp3("https://www.youtube.com/watch?v=abc123")


def test_youtu_be_url_accepted():
    """youtu.be short URLs should pass the URL validation check."""
    from musicprod.tools.youtube_to_mp3 import download_youtube_to_mp3

    # Only test that the URL passes validation (no network call needed).
    # We patch yt_dlp to avoid an actual download.
    with patch("musicprod.tools.youtube_to_mp3.yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"title": "Short"}
        mock_ydl_cls.return_value = mock_ydl

        result = download_youtube_to_mp3("https://youtu.be/abc123")
        assert result.suffix == ".mp3"
