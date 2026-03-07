"""Tests for musicprod.tools.audio_normalizer."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


def test_file_not_found():
    from musicprod.tools.audio_normalizer import normalize_audio

    with pytest.raises(FileNotFoundError, match="not found"):
        normalize_audio("/non/existent/file.mp3")


def test_invalid_target_dbfs(tmp_path):
    from musicprod.tools.audio_normalizer import normalize_audio

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="must be <= 0"):
        normalize_audio(str(src), target_dbfs=1.0)


def test_normalize_writes_output(tmp_path):
    from musicprod.tools.audio_normalizer import normalize_audio

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    mock_audio = MagicMock()
    mock_audio.dBFS = -20.0
    mock_normalized = MagicMock()
    mock_audio.apply_gain.return_value = mock_normalized

    with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
        result = normalize_audio(str(src))

    assert "_normalized" in result.name
    mock_audio.apply_gain.assert_called_once_with(-14.0 - (-20.0))
    mock_normalized.export.assert_called_once()


def test_normalize_custom_output(tmp_path):
    from musicprod.tools.audio_normalizer import normalize_audio

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)
    dest = tmp_path / "out.mp3"

    mock_audio = MagicMock()
    mock_audio.dBFS = -18.0
    mock_normalized = MagicMock()
    mock_audio.apply_gain.return_value = mock_normalized

    with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
        result = normalize_audio(str(src), target_dbfs=-14.0, output_path=str(dest))

    assert result == dest.resolve()


def test_normalize_custom_dbfs(tmp_path):
    from musicprod.tools.audio_normalizer import normalize_audio

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    mock_audio = MagicMock()
    mock_audio.dBFS = -20.0
    mock_normalized = MagicMock()
    mock_audio.apply_gain.return_value = mock_normalized

    with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
        normalize_audio(str(src), target_dbfs=-6.0)

    mock_audio.apply_gain.assert_called_once_with(-6.0 - (-20.0))


def test_load_error_raises_runtime(tmp_path):
    from musicprod.tools.audio_normalizer import normalize_audio

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    with patch("pydub.AudioSegment.from_file", side_effect=Exception("codec error")):
        with pytest.raises(RuntimeError, match="Failed to load audio"):
            normalize_audio(str(src))
