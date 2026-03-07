"""Tests for musicprod.tools.fade_effect."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


def test_file_not_found():
    from musicprod.tools.fade_effect import add_fade

    with pytest.raises(FileNotFoundError, match="not found"):
        add_fade("/non/existent/file.mp3", fade_in=1.0)


def test_negative_fade_in(tmp_path):
    from musicprod.tools.fade_effect import add_fade

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="fade_in must be >= 0"):
        add_fade(str(src), fade_in=-1.0)


def test_negative_fade_out(tmp_path):
    from musicprod.tools.fade_effect import add_fade

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="fade_out must be >= 0"):
        add_fade(str(src), fade_out=-2.0)


def test_both_zero_raises(tmp_path):
    from musicprod.tools.fade_effect import add_fade

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="At least one"):
        add_fade(str(src), fade_in=0.0, fade_out=0.0)


def test_fade_exceeds_duration(tmp_path):
    from musicprod.tools.fade_effect import add_fade

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    mock_audio = MagicMock()
    mock_audio.__len__ = MagicMock(return_value=3000)  # 3 seconds

    with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
        with pytest.raises(ValueError, match="Combined fade duration"):
            add_fade(str(src), fade_in=2.0, fade_out=2.0)


def test_add_fade_success(tmp_path):
    from musicprod.tools.fade_effect import add_fade

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    mock_audio = MagicMock()
    mock_audio.__len__ = MagicMock(return_value=10000)  # 10 seconds
    mock_faded = MagicMock()
    mock_audio.fade_out.return_value = mock_faded

    with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
        result = add_fade(str(src), fade_out=2.0)

    assert "_faded" in result.name
    mock_audio.fade_out.assert_called_once_with(2000)
    mock_faded.export.assert_called_once()


def test_add_fade_in_and_out(tmp_path):
    from musicprod.tools.fade_effect import add_fade

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    mock_audio = MagicMock()
    mock_audio.__len__ = MagicMock(return_value=10000)
    mock_after_in = MagicMock()
    mock_after_out = MagicMock()
    mock_audio.fade_in.return_value = mock_after_in
    mock_after_in.fade_out.return_value = mock_after_out

    with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
        result = add_fade(str(src), fade_in=1.0, fade_out=2.0)

    mock_audio.fade_in.assert_called_once_with(1000)
    mock_after_in.fade_out.assert_called_once_with(2000)
    mock_after_out.export.assert_called_once()


def test_load_error_raises_runtime(tmp_path):
    from musicprod.tools.fade_effect import add_fade

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    with patch("pydub.AudioSegment.from_file", side_effect=Exception("codec error")):
        with pytest.raises(RuntimeError, match="Failed to load audio"):
            add_fade(str(src), fade_out=1.0)
