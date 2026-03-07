"""Tests for musicprod.tools.pitch_shifter."""

from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import MagicMock, patch


def test_file_not_found():
    from musicprod.tools.pitch_shifter import shift_pitch

    with pytest.raises(FileNotFoundError, match="not found"):
        shift_pitch("/non/existent/file.mp3", semitones=2)


def test_shift_writes_output(tmp_path):
    from musicprod.tools.pitch_shifter import shift_pitch

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    fake_y = np.zeros(22050, dtype=np.float32)
    fake_sr = 22050

    with (
        patch("librosa.load", return_value=(fake_y, fake_sr)),
        patch("librosa.effects.pitch_shift", return_value=fake_y),
        patch("pydub.AudioSegment") as mock_seg_cls,
    ):
        mock_seg = MagicMock()
        mock_seg_cls.return_value = mock_seg
        result = shift_pitch(str(src), semitones=2)

    assert "_pitched" in result.name
    mock_seg.export.assert_called_once()


def test_shift_custom_output(tmp_path):
    from musicprod.tools.pitch_shifter import shift_pitch

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)
    dest = tmp_path / "high.mp3"

    fake_y = np.zeros(22050, dtype=np.float32)
    fake_sr = 22050

    with (
        patch("librosa.load", return_value=(fake_y, fake_sr)),
        patch("librosa.effects.pitch_shift", return_value=fake_y),
        patch("pydub.AudioSegment") as mock_seg_cls,
    ):
        mock_seg = MagicMock()
        mock_seg_cls.return_value = mock_seg
        result = shift_pitch(str(src), semitones=-1, output_path=str(dest))

    assert result == dest.resolve()


def test_shift_error_raises_runtime(tmp_path):
    from musicprod.tools.pitch_shifter import shift_pitch

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    with patch("librosa.load", side_effect=Exception("load error")):
        with pytest.raises(RuntimeError, match="Pitch shift failed"):
            shift_pitch(str(src), semitones=3)


def test_shift_output_without_extension_gets_source_ext(tmp_path):
    """Regression: output path without extension must inherit the source extension."""
    from musicprod.tools.pitch_shifter import shift_pitch

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)
    # Provide an output path that has NO extension
    dest_no_ext = str(tmp_path / "my_pitched_song")

    fake_y = np.zeros(22050, dtype=np.float32)
    fake_sr = 22050

    with (
        patch("librosa.load", return_value=(fake_y, fake_sr)),
        patch("librosa.effects.pitch_shift", return_value=fake_y),
        patch("pydub.AudioSegment") as mock_seg_cls,
    ):
        mock_seg = MagicMock()
        mock_seg_cls.return_value = mock_seg
        result = shift_pitch(str(src), semitones=2, output_path=dest_no_ext)

    # The result must have a file extension — the source's .mp3
    assert result.suffix == ".mp3", f"Expected .mp3 suffix, got {result.suffix!r}"
    # The stem must still be the one the user requested
    assert result.stem == "my_pitched_song"
    # pydub should have been told to export as mp3
    _, export_kwargs = mock_seg.export.call_args
    assert export_kwargs.get("format") == "mp3"


def test_shift_default_output_always_has_extension(tmp_path):
    """Default output path must have the same extension as the source."""
    from musicprod.tools.pitch_shifter import shift_pitch

    src = tmp_path / "track.wav"
    src.write_bytes(b"\x00" * 64)

    fake_y = np.zeros(22050, dtype=np.float32)
    fake_sr = 22050

    with (
        patch("librosa.load", return_value=(fake_y, fake_sr)),
        patch("librosa.effects.pitch_shift", return_value=fake_y),
        patch("pydub.AudioSegment") as mock_seg_cls,
    ):
        mock_seg = MagicMock()
        mock_seg_cls.return_value = mock_seg
        result = shift_pitch(str(src), semitones=-2)

    assert result.suffix == ".wav"
