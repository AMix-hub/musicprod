"""Tests for musicprod.tools.audio_trimmer."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# _parse_time
# ---------------------------------------------------------------------------

def test_parse_time_int():
    from musicprod.tools.audio_trimmer import _parse_time

    assert _parse_time(30) == 30.0


def test_parse_time_float():
    from musicprod.tools.audio_trimmer import _parse_time

    assert _parse_time(1.5) == 1.5


def test_parse_time_seconds_string():
    from musicprod.tools.audio_trimmer import _parse_time

    assert _parse_time("90") == 90.0


def test_parse_time_mm_ss():
    from musicprod.tools.audio_trimmer import _parse_time

    assert _parse_time("1:30") == 90.0


def test_parse_time_hh_mm_ss():
    from musicprod.tools.audio_trimmer import _parse_time

    assert _parse_time("1:01:01") == 3661.0


def test_parse_time_invalid():
    from musicprod.tools.audio_trimmer import _parse_time

    with pytest.raises(ValueError, match="Unrecognised time format"):
        _parse_time("bad")


# ---------------------------------------------------------------------------
# trim_audio
# ---------------------------------------------------------------------------

def test_file_not_found():
    from musicprod.tools.audio_trimmer import trim_audio

    with pytest.raises(FileNotFoundError, match="not found"):
        trim_audio("/non/existent/file.mp3", 0, 10)


def test_start_after_end_raises(tmp_path):
    from musicprod.tools.audio_trimmer import trim_audio

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="must be less than"):
        trim_audio(str(src), 30, 10)


def test_end_exceeds_duration_raises(tmp_path):
    from musicprod.tools.audio_trimmer import trim_audio

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    mock_audio = MagicMock()
    mock_audio.__len__ = MagicMock(return_value=10_000)  # 10 seconds

    with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
        with pytest.raises(ValueError, match="exceeds file duration"):
            trim_audio(str(src), 0, 20)


def test_trim_writes_output(tmp_path):
    from musicprod.tools.audio_trimmer import trim_audio

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    mock_audio = MagicMock()
    mock_audio.__len__ = MagicMock(return_value=60_000)  # 60 seconds
    mock_segment = MagicMock()
    mock_audio.__getitem__ = MagicMock(return_value=mock_segment)

    with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
        result = trim_audio(str(src), 0, 30)

    assert "_trimmed" in result.name
    mock_segment.export.assert_called_once()


def test_trim_custom_output(tmp_path):
    from musicprod.tools.audio_trimmer import trim_audio

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)
    dest = tmp_path / "cut.mp3"

    mock_audio = MagicMock()
    mock_audio.__len__ = MagicMock(return_value=60_000)
    mock_segment = MagicMock()
    mock_audio.__getitem__ = MagicMock(return_value=mock_segment)

    with patch("pydub.AudioSegment.from_file", return_value=mock_audio):
        result = trim_audio(str(src), "0:10", "0:30", output_path=str(dest))

    assert result == dest.resolve()
