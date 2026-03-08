"""Tests for musicprod.tools.noise_reducer."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


def test_file_not_found():
    from musicprod.tools.noise_reducer import reduce_noise

    with pytest.raises(FileNotFoundError, match="not found"):
        reduce_noise("/non/existent/file.wav")


def test_invalid_noise_duration(tmp_path):
    from musicprod.tools.noise_reducer import reduce_noise

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="noise_duration must be > 0"):
        reduce_noise(str(src), noise_duration=0)


def test_invalid_strength(tmp_path):
    from musicprod.tools.noise_reducer import reduce_noise

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="strength must be >= 0"):
        reduce_noise(str(src), strength=-1.0)


def test_reduce_noise_success(tmp_path):
    import numpy as np
    from musicprod.tools.noise_reducer import reduce_noise

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)
    dest = tmp_path / "audio_denoised.wav"

    mock_y = np.zeros(44100)
    mock_sr = 44100

    with patch("librosa.load", return_value=(mock_y, mock_sr)), \
         patch("soundfile.write") as mock_write:
        result = reduce_noise(str(src))

    assert "_denoised" in result.name
    mock_write.assert_called_once()


def test_reduce_noise_custom_output(tmp_path):
    import numpy as np
    from musicprod.tools.noise_reducer import reduce_noise

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)
    dest = tmp_path / "out.wav"

    mock_y = np.zeros(44100)
    mock_sr = 44100

    with patch("librosa.load", return_value=(mock_y, mock_sr)), \
         patch("soundfile.write") as mock_write:
        result = reduce_noise(str(src), output_path=str(dest))

    assert result == dest.resolve()


def test_reduce_noise_runtime_error(tmp_path):
    from musicprod.tools.noise_reducer import reduce_noise

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with patch("librosa.load", side_effect=Exception("codec error")):
        with pytest.raises(RuntimeError, match="Noise reduction failed"):
            reduce_noise(str(src))


def test_reduce_noise_wiener_method(tmp_path):
    """method='wiener' runs without error and produces output."""
    import numpy as np
    from musicprod.tools.noise_reducer import reduce_noise

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    mock_y = np.zeros(44100)
    mock_sr = 44100

    with patch("librosa.load", return_value=(mock_y, mock_sr)), \
         patch("soundfile.write") as mock_write:
        result = reduce_noise(str(src), method="wiener")

    assert "_denoised" in result.name
    mock_write.assert_called_once()


def test_reduce_noise_subtract_method(tmp_path):
    """method='subtract' runs without error and produces output."""
    import numpy as np
    from musicprod.tools.noise_reducer import reduce_noise

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    mock_y = np.zeros(44100)
    mock_sr = 44100

    with patch("librosa.load", return_value=(mock_y, mock_sr)), \
         patch("soundfile.write") as mock_write:
        result = reduce_noise(str(src), method="subtract")

    mock_write.assert_called_once()


def test_reduce_noise_invalid_method(tmp_path):
    """Unknown method raises ValueError."""
    from musicprod.tools.noise_reducer import reduce_noise

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="method must be"):
        reduce_noise(str(src), method="magic")


def test_reduce_noise_spectral_floor_validation(tmp_path):
    """spectral_floor outside [0,1] raises ValueError."""
    from musicprod.tools.noise_reducer import reduce_noise

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="spectral_floor"):
        reduce_noise(str(src), spectral_floor=1.5)
