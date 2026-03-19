"""Tests for musicprod.tools.harmonic_exciter."""

from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Saturation helper unit tests
# ---------------------------------------------------------------------------

def test_saturate_tube_preserves_sign():
    from musicprod.tools.harmonic_exciter import _saturate_tube
    x = np.array([-0.5, 0.0, 0.5])
    y = _saturate_tube(x, drive=0.5)
    assert y[0] < 0
    assert y[1] == pytest.approx(0.0, abs=1e-9)
    assert y[2] > 0


def test_saturate_tape_preserves_sign():
    from musicprod.tools.harmonic_exciter import _saturate_tape
    x = np.array([-0.5, 0.0, 0.5])
    y = _saturate_tape(x, drive=0.5)
    assert y[0] < 0
    assert y[1] == pytest.approx(0.0, abs=1e-9)
    assert y[2] > 0


def test_saturate_transistor_preserves_sign():
    from musicprod.tools.harmonic_exciter import _saturate_transistor
    x = np.array([-0.5, 0.0, 0.5])
    y = _saturate_transistor(x, drive=0.5)
    assert y[0] < 0
    assert y[1] == pytest.approx(0.0, abs=1e-9)
    assert y[2] > 0


def test_saturate_zero_drive_tube():
    """At drive=0 the tube saturator still softly saturates (non-linear output)."""
    from musicprod.tools.harmonic_exciter import _saturate_tube
    x = np.linspace(-0.5, 0.5, 100)
    y = _saturate_tube(x, drive=0.0)
    # The saturator is still non-linear at drive=0 (exponent=1 → y=x/(1+|x|)).
    # Output should be finite, non-empty, and have the correct sign structure.
    assert np.all(np.isfinite(y))
    assert y[0] < 0       # negative half stays negative
    assert y[-1] > 0      # positive half stays positive
    # The peak is reduced relative to input (soft clip)
    assert np.max(np.abs(y)) < np.max(np.abs(x))


def test_saturate_zero_input():
    from musicprod.tools.harmonic_exciter import _saturate_tube, _saturate_tape, _saturate_transistor
    x = np.zeros(100)
    assert np.allclose(_saturate_tube(x, 1.0), 0.0)
    assert np.allclose(_saturate_tape(x, 1.0), 0.0)
    assert np.allclose(_saturate_transistor(x, 1.0), 0.0)


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

def test_file_not_found():
    from musicprod.tools.harmonic_exciter import excite

    with pytest.raises(FileNotFoundError, match="not found"):
        excite("/non/existent/file.wav")


def test_invalid_drive(tmp_path):
    from musicprod.tools.harmonic_exciter import excite

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="drive must be between"):
        excite(str(src), drive=1.5)


def test_invalid_blend(tmp_path):
    from musicprod.tools.harmonic_exciter import excite

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="blend must be between"):
        excite(str(src), blend=-0.1)


def test_invalid_mode(tmp_path):
    from musicprod.tools.harmonic_exciter import excite

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="mode must be one of"):
        excite(str(src), mode="valve")


def test_invalid_freq_band(tmp_path):
    from musicprod.tools.harmonic_exciter import excite

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="freq_band must be one of"):
        excite(str(src), freq_band="mids")


def test_invalid_band_cutoff(tmp_path):
    from musicprod.tools.harmonic_exciter import excite

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="band_cutoff must be > 0"):
        excite(str(src), band_cutoff=0.0)


# ---------------------------------------------------------------------------
# Success paths (all modes and bands)
# ---------------------------------------------------------------------------

def _run_excite(tmp_path, **kwargs):
    from musicprod.tools.harmonic_exciter import excite

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    mock_y = np.random.default_rng(0).uniform(-0.5, 0.5, 44100).astype(np.float32)
    mock_sr = 44100

    with patch("librosa.load", return_value=(mock_y, mock_sr)), \
         patch("soundfile.write") as mock_write:
        result = excite(str(src), **kwargs)

    return result, mock_write


def test_excite_tube_highs(tmp_path):
    result, mock_write = _run_excite(tmp_path, mode="tube", freq_band="highs")
    assert "_excited" in result.name
    mock_write.assert_called_once()


def test_excite_tape_lows(tmp_path):
    result, mock_write = _run_excite(tmp_path, mode="tape", freq_band="lows")
    assert "_excited" in result.name
    mock_write.assert_called_once()


def test_excite_transistor_full(tmp_path):
    result, mock_write = _run_excite(tmp_path, mode="transistor", freq_band="full")
    assert "_excited" in result.name
    mock_write.assert_called_once()


def test_excite_stereo(tmp_path):
    from musicprod.tools.harmonic_exciter import excite

    src = tmp_path / "stereo.wav"
    src.write_bytes(b"\x00" * 64)

    mock_y = np.random.default_rng(0).uniform(-0.5, 0.5, (2, 44100)).astype(np.float32)
    mock_sr = 44100

    with patch("librosa.load", return_value=(mock_y, mock_sr)), \
         patch("soundfile.write") as mock_write:
        result = excite(str(src), mode="tube")

    assert "_excited" in result.name
    mock_write.assert_called_once()


def test_excite_custom_output(tmp_path):
    from musicprod.tools.harmonic_exciter import excite

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)
    dest = tmp_path / "out.wav"

    mock_y = np.zeros(44100)
    mock_sr = 44100

    with patch("librosa.load", return_value=(mock_y, mock_sr)), \
         patch("soundfile.write"):
        result = excite(str(src), output_path=str(dest))

    assert result == dest.resolve()


def test_excite_mp3_fallback_to_wav(tmp_path):
    from musicprod.tools.harmonic_exciter import excite

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    mock_y = np.zeros(44100)
    mock_sr = 44100

    with patch("librosa.load", return_value=(mock_y, mock_sr)), \
         patch("soundfile.write"):
        result = excite(str(src))

    assert result.suffix == ".wav"


def test_excite_blend_zero_returns_dry_level(tmp_path):
    """blend=0 should output essentially the dry signal (no saturation applied)."""
    from musicprod.tools.harmonic_exciter import excite

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    rng = np.random.default_rng(1)
    mock_y = rng.uniform(-0.5, 0.5, 44100).astype(np.float64)
    mock_sr = 44100

    written_data: list = []

    def capture_write(path, data, sr):
        written_data.append(data.copy())

    with patch("librosa.load", return_value=(mock_y, mock_sr)), \
         patch("soundfile.write", side_effect=capture_write):
        excite(str(src), blend=0.0, freq_band="full")

    assert len(written_data) == 1
    np.testing.assert_allclose(written_data[0], mock_y, atol=1e-4)


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------

def test_excite_runtime_error(tmp_path):
    from musicprod.tools.harmonic_exciter import excite

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with patch("librosa.load", side_effect=Exception("codec error")):
        with pytest.raises(RuntimeError, match="Harmonic excitation failed"):
            excite(str(src))
