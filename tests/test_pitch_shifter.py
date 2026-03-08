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

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    fake_y = np.zeros(22050, dtype=np.float32)
    fake_sr = 22050

    with patch("librosa.load", return_value=(fake_y, fake_sr)), \
         patch("librosa.effects.pitch_shift", return_value=fake_y), \
         patch("soundfile.write") as mock_write:
        result = shift_pitch(str(src), semitones=2)

    assert "_pitched" in result.name
    mock_write.assert_called_once()


def test_shift_custom_output(tmp_path):
    from musicprod.tools.pitch_shifter import shift_pitch

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)
    dest = tmp_path / "high.wav"

    fake_y = np.zeros(22050, dtype=np.float32)
    fake_sr = 22050

    with patch("librosa.load", return_value=(fake_y, fake_sr)), \
         patch("librosa.effects.pitch_shift", return_value=fake_y), \
         patch("soundfile.write"):
        result = shift_pitch(str(src), semitones=-1, output_path=str(dest))

    assert result == dest.resolve()


def test_shift_error_raises_runtime(tmp_path):
    from musicprod.tools.pitch_shifter import shift_pitch

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with patch("librosa.load", side_effect=Exception("load error")):
        with pytest.raises(RuntimeError, match="Pitch shift failed"):
            shift_pitch(str(src), semitones=3)


def test_shift_mp3_falls_back_to_wav(tmp_path):
    """MP3 source with default output path must produce a .wav file."""
    from musicprod.tools.pitch_shifter import shift_pitch

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    fake_y = np.zeros(22050, dtype=np.float32)
    fake_sr = 22050

    with patch("librosa.load", return_value=(fake_y, fake_sr)), \
         patch("librosa.effects.pitch_shift", return_value=fake_y), \
         patch("soundfile.write"):
        result = shift_pitch(str(src), semitones=2)

    assert result.suffix == ".wav"


def test_shift_default_output_wav_keeps_extension(tmp_path):
    """Default output path for a .wav source has a .wav extension."""
    from musicprod.tools.pitch_shifter import shift_pitch

    src = tmp_path / "track.wav"
    src.write_bytes(b"\x00" * 64)

    fake_y = np.zeros(22050, dtype=np.float32)
    fake_sr = 22050

    with patch("librosa.load", return_value=(fake_y, fake_sr)), \
         patch("librosa.effects.pitch_shift", return_value=fake_y), \
         patch("soundfile.write"):
        result = shift_pitch(str(src), semitones=-2)

    assert result.suffix == ".wav"


def test_shift_stereo(tmp_path):
    """Stereo audio is processed without error (two channels)."""
    from musicprod.tools.pitch_shifter import shift_pitch

    src = tmp_path / "stereo.wav"
    src.write_bytes(b"\x00" * 64)

    # Shape (2, T) = stereo
    fake_y = np.zeros((2, 22050), dtype=np.float32)
    fake_sr = 22050
    fake_shifted = np.zeros(22050, dtype=np.float32)

    with patch("librosa.load", return_value=(fake_y, fake_sr)), \
         patch("librosa.effects.pitch_shift", return_value=fake_shifted), \
         patch("soundfile.write") as mock_write:
        result = shift_pitch(str(src), semitones=2)

    assert "_pitched" in result.name
    mock_write.assert_called_once()


def test_shift_preserve_formants_flag(tmp_path):
    """preserve_formants=True runs without error."""
    from musicprod.tools.pitch_shifter import shift_pitch

    src = tmp_path / "vocal.wav"
    src.write_bytes(b"\x00" * 64)

    fake_y = np.zeros(22050, dtype=np.float32)
    fake_sr = 22050

    with patch("librosa.load", return_value=(fake_y, fake_sr)), \
         patch("librosa.effects.pitch_shift", return_value=fake_y), \
         patch("librosa.stft", return_value=np.zeros((1025, 43), dtype=complex)), \
         patch("librosa.istft", return_value=fake_y), \
         patch("soundfile.write") as mock_write:
        result = shift_pitch(str(src), semitones=3, preserve_formants=True)

    assert "_pitched" in result.name
    mock_write.assert_called_once()
