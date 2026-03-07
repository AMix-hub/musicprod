"""Tests for musicprod.tools.format_converter."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


def test_file_not_found():
    from musicprod.tools.format_converter import convert_format

    with pytest.raises(FileNotFoundError, match="not found"):
        convert_format("/non/existent/file.wav", "mp3")


def test_unsupported_format(tmp_path):
    from musicprod.tools.format_converter import convert_format

    dummy = tmp_path / "audio.wav"
    dummy.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="Unsupported format"):
        convert_format(str(dummy), "xyz")


def test_convert_writes_output(tmp_path):
    from musicprod.tools.format_converter import convert_format

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    mock_audio = MagicMock()
    with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
        result = convert_format(str(src), "mp3")

    assert result.suffix == ".mp3"
    mock_audio.export.assert_called_once()


def test_custom_output_path(tmp_path):
    from musicprod.tools.format_converter import convert_format

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)
    dest = tmp_path / "converted.flac"

    mock_audio = MagicMock()
    with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
        result = convert_format(str(src), "flac", output_path=str(dest))

    assert result == dest.resolve()


def test_pydub_error_raises_runtime_error(tmp_path):
    from musicprod.tools.format_converter import convert_format

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with patch("pydub.AudioSegment.from_file", side_effect=Exception("codec error")):
        with pytest.raises(RuntimeError, match="Format conversion failed"):
            convert_format(str(src), "mp3")
