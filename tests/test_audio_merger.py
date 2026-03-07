"""Tests for musicprod.tools.audio_merger."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


def test_too_few_files():
    from musicprod.tools.audio_merger import merge_audio

    with pytest.raises(ValueError, match="At least two"):
        merge_audio(["/some/file.mp3"])


def test_file_not_found(tmp_path):
    from musicprod.tools.audio_merger import merge_audio

    existing = tmp_path / "a.mp3"
    existing.write_bytes(b"\x00" * 64)

    with pytest.raises(FileNotFoundError, match="not found"):
        merge_audio([str(existing), "/non/existent/b.mp3"])


def test_merge_writes_output(tmp_path):
    from musicprod.tools.audio_merger import merge_audio

    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    a.write_bytes(b"\x00" * 64)
    b.write_bytes(b"\x00" * 64)

    mock_seg_a = MagicMock()
    mock_seg_b = MagicMock()
    mock_combined = MagicMock()
    mock_seg_a.__add__ = MagicMock(return_value=mock_combined)

    with patch("pydub.AudioSegment.from_file", side_effect=[mock_seg_a, mock_seg_b]):
        result = merge_audio([str(a), str(b)])

    assert result.name == "merged.mp3"
    mock_combined.export.assert_called_once()


def test_merge_custom_output(tmp_path):
    from musicprod.tools.audio_merger import merge_audio

    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    a.write_bytes(b"\x00" * 64)
    b.write_bytes(b"\x00" * 64)
    dest = tmp_path / "full.mp3"

    mock_seg_a = MagicMock()
    mock_seg_b = MagicMock()
    mock_combined = MagicMock()
    mock_seg_a.__add__ = MagicMock(return_value=mock_combined)

    with patch("pydub.AudioSegment.from_file", side_effect=[mock_seg_a, mock_seg_b]):
        result = merge_audio([str(a), str(b)], output_path=str(dest))

    assert result == dest.resolve()


def test_merge_three_files(tmp_path):
    from musicprod.tools.audio_merger import merge_audio

    files = []
    for name in ["a.mp3", "b.mp3", "c.mp3"]:
        f = tmp_path / name
        f.write_bytes(b"\x00" * 64)
        files.append(str(f))

    mock_segs = [MagicMock() for _ in range(3)]
    mock_combined_1 = MagicMock()
    mock_combined_2 = MagicMock()
    mock_segs[0].__add__ = MagicMock(return_value=mock_combined_1)
    mock_combined_1.__add__ = MagicMock(return_value=mock_combined_2)

    with patch("pydub.AudioSegment.from_file", side_effect=mock_segs):
        result = merge_audio(files)

    assert result.name == "merged.mp3"
    mock_combined_2.export.assert_called_once()


def test_merge_load_error(tmp_path):
    from musicprod.tools.audio_merger import merge_audio

    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    a.write_bytes(b"\x00" * 64)
    b.write_bytes(b"\x00" * 64)

    with patch("pydub.AudioSegment.from_file", side_effect=Exception("codec error")):
        with pytest.raises(RuntimeError, match="Failed to merge audio"):
            merge_audio([str(a), str(b)])
