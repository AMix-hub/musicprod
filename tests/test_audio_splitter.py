"""Tests for musicprod.tools.audio_splitter."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, call, patch


def test_file_not_found():
    from musicprod.tools.audio_splitter import split_audio

    with pytest.raises(FileNotFoundError, match="not found"):
        split_audio("/non/existent/file.mp3", chunk_duration=30)


def test_invalid_chunk_duration(tmp_path):
    from musicprod.tools.audio_splitter import split_audio

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="must be positive"):
        split_audio(str(src), chunk_duration=0)


def test_invalid_negative_chunk_duration(tmp_path):
    from musicprod.tools.audio_splitter import split_audio

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="must be positive"):
        split_audio(str(src), chunk_duration=-5)


def test_split_creates_chunks(tmp_path):
    from musicprod.tools.audio_splitter import split_audio

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    # 90-second audio, 30-second chunks → 3 chunks
    mock_audio = MagicMock()
    mock_audio.__len__ = MagicMock(return_value=90_000)
    mock_chunk = MagicMock()
    mock_audio.__getitem__ = MagicMock(return_value=mock_chunk)

    with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
        chunks = split_audio(str(src), chunk_duration=30)

    assert len(chunks) == 3
    assert mock_chunk.export.call_count == 3
    for chunk_path in chunks:
        assert "_part" in chunk_path.name


def test_split_custom_output_dir(tmp_path):
    from musicprod.tools.audio_splitter import split_audio

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)
    out_dir = tmp_path / "chunks"

    mock_audio = MagicMock()
    mock_audio.__len__ = MagicMock(return_value=60_000)
    mock_chunk = MagicMock()
    mock_audio.__getitem__ = MagicMock(return_value=mock_chunk)

    with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
        chunks = split_audio(str(src), chunk_duration=30, output_dir=str(out_dir))

    assert len(chunks) == 2
    for chunk_path in chunks:
        assert chunk_path.parent == out_dir


def test_split_load_error(tmp_path):
    from musicprod.tools.audio_splitter import split_audio

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    with patch("pydub.AudioSegment.from_file", side_effect=Exception("codec error")):
        with pytest.raises(RuntimeError, match="Failed to load audio"):
            split_audio(str(src), chunk_duration=30)
