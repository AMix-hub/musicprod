"""Tests for musicprod.tools.spectral_analyzer."""

from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Validation tests (no I/O required)
# ---------------------------------------------------------------------------

def test_file_not_found():
    from musicprod.tools.spectral_analyzer import analyze_spectrum

    with pytest.raises(FileNotFoundError, match="not found"):
        analyze_spectrum("/non/existent/file.wav")


def test_invalid_n_mels(tmp_path):
    from musicprod.tools.spectral_analyzer import analyze_spectrum

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="n_mels must be >= 1"):
        analyze_spectrum(str(src), n_mels=0)


def test_invalid_n_fft(tmp_path):
    from musicprod.tools.spectral_analyzer import analyze_spectrum

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="n_fft must be >= 1"):
        analyze_spectrum(str(src), n_fft=0)


def test_invalid_hop_length(tmp_path):
    from musicprod.tools.spectral_analyzer import analyze_spectrum

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="hop_length must be >= 1"):
        analyze_spectrum(str(src), hop_length=0)


def test_invalid_fmin(tmp_path):
    from musicprod.tools.spectral_analyzer import analyze_spectrum

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="fmin must be >= 0"):
        analyze_spectrum(str(src), fmin=-10.0)


def test_invalid_top_db(tmp_path):
    from musicprod.tools.spectral_analyzer import analyze_spectrum

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="top_db must be > 0"):
        analyze_spectrum(str(src), top_db=0.0)


def test_invalid_width(tmp_path):
    from musicprod.tools.spectral_analyzer import analyze_spectrum

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="width must be >= 100"):
        analyze_spectrum(str(src), width=50)


def test_invalid_height(tmp_path):
    from musicprod.tools.spectral_analyzer import analyze_spectrum

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="height must be >= 100"):
        analyze_spectrum(str(src), height=50)


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------

def _make_mock_fig():
    """Return a lightweight mock matplotlib Figure."""
    fig = MagicMock()
    fig.get_facecolor.return_value = "#0d0d0d"
    fig.add_subplot.return_value = MagicMock()
    fig.suptitle.return_value = None
    return fig


def test_analyze_spectrum_default_output(tmp_path):
    from musicprod.tools.spectral_analyzer import analyze_spectrum

    src = tmp_path / "song.wav"
    src.write_bytes(b"\x00" * 64)

    n_frames = 10
    mock_y = np.zeros(22050)
    mock_sr = 44100
    mock_mel = np.zeros((128, n_frames))
    mock_chroma = np.zeros((12, n_frames))
    mock_centroid = np.zeros((1, n_frames))
    mock_rms = np.zeros((1, n_frames))
    mock_times = np.linspace(0, 0.5, n_frames)

    with patch("librosa.load", return_value=(mock_y, mock_sr)), \
         patch("librosa.get_duration", return_value=0.5), \
         patch("librosa.feature.melspectrogram", return_value=mock_mel), \
         patch("librosa.power_to_db", return_value=mock_mel), \
         patch("librosa.feature.chroma_cqt", return_value=mock_chroma), \
         patch("librosa.feature.spectral_centroid", return_value=mock_centroid), \
         patch("librosa.feature.rms", return_value=mock_rms), \
         patch("librosa.frames_to_time", return_value=mock_times), \
         patch("librosa.amplitude_to_db", return_value=mock_rms[0]), \
         patch("matplotlib.pyplot.figure", return_value=_make_mock_fig()), \
         patch("matplotlib.pyplot.close"), \
         patch("librosa.display.specshow", return_value=MagicMock()):
        result = analyze_spectrum(str(src))

    assert "_analysis" in result.name
    assert result.suffix == ".png"


def test_analyze_spectrum_custom_output(tmp_path):
    from musicprod.tools.spectral_analyzer import analyze_spectrum

    src = tmp_path / "song.wav"
    src.write_bytes(b"\x00" * 64)
    out = tmp_path / "custom_out.png"

    n_frames = 10
    mock_y = np.zeros(22050)
    mock_sr = 44100
    mock_mel = np.zeros((128, n_frames))
    mock_chroma = np.zeros((12, n_frames))
    mock_centroid = np.zeros((1, n_frames))
    mock_rms = np.zeros((1, n_frames))
    mock_times = np.linspace(0, 0.5, n_frames)

    with patch("librosa.load", return_value=(mock_y, mock_sr)), \
         patch("librosa.get_duration", return_value=0.5), \
         patch("librosa.feature.melspectrogram", return_value=mock_mel), \
         patch("librosa.power_to_db", return_value=mock_mel), \
         patch("librosa.feature.chroma_cqt", return_value=mock_chroma), \
         patch("librosa.feature.spectral_centroid", return_value=mock_centroid), \
         patch("librosa.feature.rms", return_value=mock_rms), \
         patch("librosa.frames_to_time", return_value=mock_times), \
         patch("librosa.amplitude_to_db", return_value=mock_rms[0]), \
         patch("matplotlib.pyplot.figure", return_value=_make_mock_fig()), \
         patch("matplotlib.pyplot.close"), \
         patch("librosa.display.specshow", return_value=MagicMock()):
        result = analyze_spectrum(str(src), output_path=str(out))

    assert result == out.resolve()


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------

def test_analyze_spectrum_runtime_error(tmp_path):
    from musicprod.tools.spectral_analyzer import analyze_spectrum

    src = tmp_path / "song.wav"
    src.write_bytes(b"\x00" * 64)

    with patch("librosa.load", side_effect=Exception("codec error")):
        with pytest.raises(RuntimeError, match="Spectral analysis failed"):
            analyze_spectrum(str(src))
