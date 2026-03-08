"""Tests for musicprod.tools.vocal_autotune."""

from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# _parse_scale
# ---------------------------------------------------------------------------

def test_parse_scale_chromatic():
    from musicprod.tools.vocal_autotune import _parse_scale
    pcs = _parse_scale("chromatic")
    assert pcs == list(range(12))


def test_parse_scale_c_major():
    from musicprod.tools.vocal_autotune import _parse_scale
    assert _parse_scale("C major") == [0, 2, 4, 5, 7, 9, 11]


def test_parse_scale_a_minor():
    from musicprod.tools.vocal_autotune import _parse_scale
    assert _parse_scale("A minor") == [9, 11, 0, 2, 4, 5, 7]


def test_parse_scale_flat_notation():
    from musicprod.tools.vocal_autotune import _parse_scale
    # Bb major = A# major (root semitone 10)
    bb = _parse_scale("Bb major")
    assert sorted(bb) == sorted((p + 10) % 12 for p in [0, 2, 4, 5, 7, 9, 11])


def test_parse_scale_case_insensitive():
    from musicprod.tools.vocal_autotune import _parse_scale
    assert _parse_scale("c major") == _parse_scale("C major")
    assert _parse_scale("CHROMATIC") == _parse_scale("chromatic")


def test_parse_scale_mode_only_defaults_to_c():
    from musicprod.tools.vocal_autotune import _parse_scale
    assert _parse_scale("major") == _parse_scale("C major")
    assert _parse_scale("minor") == _parse_scale("C minor")


def test_parse_scale_unknown_root_raises():
    from musicprod.tools.vocal_autotune import _parse_scale
    with pytest.raises(ValueError, match="Unknown root note"):
        _parse_scale("X major")


def test_parse_scale_unknown_mode_raises():
    from musicprod.tools.vocal_autotune import _parse_scale
    with pytest.raises(ValueError, match="Unknown mode"):
        _parse_scale("C diminished")


# ---------------------------------------------------------------------------
# _nearest_scale_midi
# ---------------------------------------------------------------------------

def test_nearest_scale_midi_exact_match():
    from musicprod.tools.vocal_autotune import _nearest_scale_midi
    # C major: [0, 2, 4, 5, 7, 9, 11]
    c_major = [0, 2, 4, 5, 7, 9, 11]
    # MIDI 60 = C4 — already in scale
    assert _nearest_scale_midi(60.0, c_major) == 60.0


def test_nearest_scale_midi_snaps_to_nearest():
    from musicprod.tools.vocal_autotune import _nearest_scale_midi
    c_major = [0, 2, 4, 5, 7, 9, 11]
    # MIDI 61 = C#4 — not in C major; nearest is C4(60) or D4(62)
    result = _nearest_scale_midi(61.0, c_major)
    assert result in (60.0, 62.0)


def test_nearest_scale_midi_chromatic_is_identity():
    from musicprod.tools.vocal_autotune import _nearest_scale_midi
    chromatic = list(range(12))
    for midi in (60.0, 61.0, 62.0, 69.0):
        assert _nearest_scale_midi(midi, chromatic) == midi


# ---------------------------------------------------------------------------
# autotune_vocals — file & parameter validation
# ---------------------------------------------------------------------------

def test_file_not_found():
    from musicprod.tools.vocal_autotune import autotune_vocals
    with pytest.raises(FileNotFoundError, match="not found"):
        autotune_vocals("/non/existent/file.wav")


def test_invalid_strength_low(tmp_path):
    from musicprod.tools.vocal_autotune import autotune_vocals
    dummy = tmp_path / "v.wav"
    dummy.write_bytes(b"\x00" * 64)
    with pytest.raises(ValueError, match="correction_strength"):
        autotune_vocals(str(dummy), correction_strength=-0.1)


def test_invalid_strength_high(tmp_path):
    from musicprod.tools.vocal_autotune import autotune_vocals
    dummy = tmp_path / "v.wav"
    dummy.write_bytes(b"\x00" * 64)
    with pytest.raises(ValueError, match="correction_strength"):
        autotune_vocals(str(dummy), correction_strength=1.1)


def test_invalid_scale_raises_value_error(tmp_path):
    from musicprod.tools.vocal_autotune import autotune_vocals
    dummy = tmp_path / "v.wav"
    dummy.write_bytes(b"\x00" * 64)
    with pytest.raises(ValueError):
        autotune_vocals(str(dummy), scale="Q bebop")


# ---------------------------------------------------------------------------
# autotune_vocals — successful processing
# ---------------------------------------------------------------------------

def _make_pyin_output(sr, hop_length, n_frames):
    """Produce fake pyin output: voiced signal at A4 (440 Hz)."""
    import librosa
    f0 = np.full(n_frames, float(librosa.note_to_hz("A4")))
    voiced_flag = np.ones(n_frames, dtype=bool)
    voiced_probs = np.ones(n_frames)
    return f0, voiced_flag, voiced_probs


def test_autotune_writes_output_file(tmp_path):
    from musicprod.tools.vocal_autotune import autotune_vocals

    src = tmp_path / "vocal.wav"
    src.write_bytes(b"\x00" * 64)

    sr = 22050
    y = np.zeros(sr * 2, dtype=np.float32)
    hop_length = 512
    n_frames = len(y) // hop_length + 1
    fake_pyin = _make_pyin_output(sr, hop_length, n_frames)

    with patch("librosa.load", return_value=(y, sr)), \
         patch("librosa.pyin", return_value=fake_pyin), \
         patch("librosa.effects.pitch_shift", return_value=y[:hop_length]), \
         patch("soundfile.write") as mock_write:
        result = autotune_vocals(str(src))

    assert "_autotuned" in result.name
    mock_write.assert_called_once()


def test_autotune_custom_output_path(tmp_path):
    from musicprod.tools.vocal_autotune import autotune_vocals

    src = tmp_path / "vocal.wav"
    src.write_bytes(b"\x00" * 64)
    dest = tmp_path / "out.wav"

    sr = 22050
    y = np.zeros(sr, dtype=np.float32)
    hop_length = 512
    n_frames = len(y) // hop_length + 1
    fake_pyin = _make_pyin_output(sr, hop_length, n_frames)

    with patch("librosa.load", return_value=(y, sr)), \
         patch("librosa.pyin", return_value=fake_pyin), \
         patch("librosa.effects.pitch_shift", return_value=y[:hop_length]), \
         patch("soundfile.write") as mock_write:
        result = autotune_vocals(str(src), output_path=str(dest))

    assert result == dest.resolve()
    mock_write.assert_called_once()


def test_autotune_mp3_falls_back_to_wav(tmp_path):
    """MP3 source with default output path must produce a .wav file."""
    from musicprod.tools.vocal_autotune import autotune_vocals

    src = tmp_path / "vocal.mp3"
    src.write_bytes(b"\x00" * 64)

    sr = 22050
    y = np.zeros(sr, dtype=np.float32)
    hop_length = 512
    n_frames = len(y) // hop_length + 1
    fake_pyin = _make_pyin_output(sr, hop_length, n_frames)

    with patch("librosa.load", return_value=(y, sr)), \
         patch("librosa.pyin", return_value=fake_pyin), \
         patch("librosa.effects.pitch_shift", return_value=y[:hop_length]), \
         patch("soundfile.write"):
        result = autotune_vocals(str(src))

    assert result.suffix == ".wav"


def test_autotune_zero_strength_no_pitch_shift_called(tmp_path):
    """With correction_strength=0 no segment should be pitch-shifted."""
    from musicprod.tools.vocal_autotune import autotune_vocals

    src = tmp_path / "vocal.wav"
    src.write_bytes(b"\x00" * 64)

    sr = 22050
    y = np.zeros(sr, dtype=np.float32)
    hop_length = 512
    n_frames = len(y) // hop_length + 1
    fake_pyin = _make_pyin_output(sr, hop_length, n_frames)

    with patch("librosa.load", return_value=(y, sr)), \
         patch("librosa.pyin", return_value=fake_pyin), \
         patch("librosa.effects.pitch_shift") as mock_shift, \
         patch("soundfile.write"):
        autotune_vocals(str(src), correction_strength=0.0)

    mock_shift.assert_not_called()


def test_autotune_empty_audio_writes_empty_file(tmp_path):
    """Zero-length audio produces an empty output file without error."""
    from musicprod.tools.vocal_autotune import autotune_vocals

    src = tmp_path / "silent.wav"
    src.write_bytes(b"\x00" * 64)

    sr = 22050
    y = np.zeros(0, dtype=np.float32)

    with patch("librosa.load", return_value=(y, sr)), \
         patch("soundfile.write") as mock_write:
        result = autotune_vocals(str(src))

    mock_write.assert_called_once()
    assert "_autotuned" in result.name


def test_autotune_unvoiced_audio_no_pitch_shift(tmp_path):
    """When PYIN reports all frames as unvoiced, no shift is applied."""
    from musicprod.tools.vocal_autotune import autotune_vocals

    src = tmp_path / "noise.wav"
    src.write_bytes(b"\x00" * 64)

    sr = 22050
    y = np.zeros(sr, dtype=np.float32)
    hop_length = 512
    n_frames = len(y) // hop_length + 1

    # All frames unvoiced
    f0 = np.full(n_frames, np.nan)
    voiced_flag = np.zeros(n_frames, dtype=bool)
    voiced_probs = np.zeros(n_frames)

    with patch("librosa.load", return_value=(y, sr)), \
         patch("librosa.pyin", return_value=(f0, voiced_flag, voiced_probs)), \
         patch("librosa.effects.pitch_shift") as mock_shift, \
         patch("soundfile.write"):
        autotune_vocals(str(src))

    mock_shift.assert_not_called()


def test_autotune_librosa_error_raises_runtime(tmp_path):
    from musicprod.tools.vocal_autotune import autotune_vocals

    src = tmp_path / "vocal.wav"
    src.write_bytes(b"\x00" * 64)

    with patch("librosa.load", side_effect=Exception("codec error")):
        with pytest.raises(RuntimeError, match="Auto-tune failed"):
            autotune_vocals(str(src))
