"""Tests for musicprod.tools.stem_splitter."""

from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


# ---------------------------------------------------------------------------
# Validation tests (no I/O required)
# ---------------------------------------------------------------------------

def test_file_not_found():
    from musicprod.tools.stem_splitter import split_stems

    with pytest.raises(FileNotFoundError, match="not found"):
        split_stems("/non/existent/file.wav")


def test_unknown_stem_raises(tmp_path):
    from musicprod.tools.stem_splitter import split_stems

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="Unknown stem"):
        split_stems(str(src), stems=["drums", "guitars"])


def test_empty_stems_raises(tmp_path):
    from musicprod.tools.stem_splitter import split_stems

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="at least one"):
        split_stems(str(src), stems=[])


def test_invalid_bass_cutoff(tmp_path):
    from musicprod.tools.stem_splitter import split_stems

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="bass_cutoff must be > 0"):
        split_stems(str(src), bass_cutoff=-1.0)


def test_invalid_hpss_margin(tmp_path):
    from musicprod.tools.stem_splitter import split_stems

    src = tmp_path / "audio.wav"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="hpss_margin must be >= 1"):
        split_stems(str(src), hpss_margin=0.5)


# ---------------------------------------------------------------------------
# Success path — mono audio
# ---------------------------------------------------------------------------

def test_split_stems_mono_all_stems(tmp_path):
    from musicprod.tools.stem_splitter import split_stems

    src = tmp_path / "track.wav"
    src.write_bytes(b"\x00" * 64)

    mock_y = np.zeros(22050)  # 0.5 s mono
    mock_sr = 44100
    mock_hpss_H = np.ones((1025, 44)) * 0.5
    mock_hpss_P = np.ones((1025, 44)) * 0.5

    with patch("librosa.load", return_value=(mock_y, mock_sr)), \
         patch("librosa.stft", return_value=np.zeros((1025, 44), dtype=complex)), \
         patch("librosa.decompose.hpss", return_value=(mock_hpss_H, mock_hpss_P)), \
         patch("librosa.istft", return_value=np.zeros(22050)), \
         patch("librosa.fft_frequencies", return_value=np.linspace(0, 22050, 1025)), \
         patch("soundfile.write") as mock_write:
        results = split_stems(str(src))

    assert set(results.keys()) == {"drums", "bass", "vocals", "other"}
    assert mock_write.call_count == 4


def test_split_stems_subset(tmp_path):
    from musicprod.tools.stem_splitter import split_stems

    src = tmp_path / "track.wav"
    src.write_bytes(b"\x00" * 64)

    mock_y = np.zeros(22050)
    mock_sr = 44100
    mock_hpss_H = np.ones((1025, 44)) * 0.5
    mock_hpss_P = np.ones((1025, 44)) * 0.5

    with patch("librosa.load", return_value=(mock_y, mock_sr)), \
         patch("librosa.stft", return_value=np.zeros((1025, 44), dtype=complex)), \
         patch("librosa.decompose.hpss", return_value=(mock_hpss_H, mock_hpss_P)), \
         patch("librosa.istft", return_value=np.zeros(22050)), \
         patch("librosa.fft_frequencies", return_value=np.linspace(0, 22050, 1025)), \
         patch("soundfile.write") as mock_write:
        results = split_stems(str(src), stems=["drums", "bass"])

    assert set(results.keys()) == {"drums", "bass"}
    assert mock_write.call_count == 2


def test_split_stems_custom_output_dir(tmp_path):
    from musicprod.tools.stem_splitter import split_stems

    src = tmp_path / "track.wav"
    src.write_bytes(b"\x00" * 64)
    out_dir = tmp_path / "my_stems"

    mock_y = np.zeros(22050)
    mock_sr = 44100
    mock_hpss_H = np.ones((1025, 44)) * 0.5
    mock_hpss_P = np.ones((1025, 44)) * 0.5

    with patch("librosa.load", return_value=(mock_y, mock_sr)), \
         patch("librosa.stft", return_value=np.zeros((1025, 44), dtype=complex)), \
         patch("librosa.decompose.hpss", return_value=(mock_hpss_H, mock_hpss_P)), \
         patch("librosa.istft", return_value=np.zeros(22050)), \
         patch("librosa.fft_frequencies", return_value=np.linspace(0, 22050, 1025)), \
         patch("soundfile.write"):
        results = split_stems(str(src), stems=["drums"], output_dir=str(out_dir))

    assert results["drums"].parent == out_dir.resolve()


# ---------------------------------------------------------------------------
# Success path — stereo audio
# ---------------------------------------------------------------------------

def test_split_stems_stereo(tmp_path):
    from musicprod.tools.stem_splitter import split_stems

    src = tmp_path / "stereo.wav"
    src.write_bytes(b"\x00" * 64)

    mock_y = np.zeros((2, 22050))  # stereo
    mock_sr = 44100
    mock_hpss_H = np.ones((1025, 44)) * 0.5
    mock_hpss_P = np.ones((1025, 44)) * 0.5

    with patch("librosa.load", return_value=(mock_y, mock_sr)), \
         patch("librosa.to_mono", return_value=np.zeros(22050)), \
         patch("librosa.stft", return_value=np.zeros((1025, 44), dtype=complex)), \
         patch("librosa.decompose.hpss", return_value=(mock_hpss_H, mock_hpss_P)), \
         patch("librosa.istft", return_value=np.zeros(22050)), \
         patch("librosa.fft_frequencies", return_value=np.linspace(0, 22050, 1025)), \
         patch("soundfile.write") as mock_write:
        results = split_stems(str(src), stems=["vocals", "other"])

    assert set(results.keys()) == {"vocals", "other"}
    assert mock_write.call_count == 2


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------

def test_split_stems_runtime_error(tmp_path):
    from musicprod.tools.stem_splitter import split_stems

    src = tmp_path / "track.wav"
    src.write_bytes(b"\x00" * 64)

    with patch("librosa.load", side_effect=Exception("codec error")):
        with pytest.raises(RuntimeError, match="Stem splitting failed"):
            split_stems(str(src))


# ---------------------------------------------------------------------------
# Output file naming
# ---------------------------------------------------------------------------

def test_stem_output_filenames(tmp_path):
    from musicprod.tools.stem_splitter import split_stems

    src = tmp_path / "my_song.wav"
    src.write_bytes(b"\x00" * 64)

    mock_y = np.zeros(22050)
    mock_sr = 44100
    mock_H = np.ones((1025, 44)) * 0.5
    mock_P = np.ones((1025, 44)) * 0.5

    with patch("librosa.load", return_value=(mock_y, mock_sr)), \
         patch("librosa.stft", return_value=np.zeros((1025, 44), dtype=complex)), \
         patch("librosa.decompose.hpss", return_value=(mock_H, mock_P)), \
         patch("librosa.istft", return_value=np.zeros(22050)), \
         patch("librosa.fft_frequencies", return_value=np.linspace(0, 22050, 1025)), \
         patch("soundfile.write"):
        results = split_stems(str(src), stems=["drums"])

    assert results["drums"].name == "my_song_drums.wav"
