"""Tests for musicprod.tools.bpm_detector."""

from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import patch


def test_file_not_found():
    from musicprod.tools.bpm_detector import detect_bpm

    with pytest.raises(FileNotFoundError, match="not found"):
        detect_bpm("/non/existent/file.mp3")


def test_returns_float(tmp_path):
    """When librosa works, detect_bpm returns a float."""
    from musicprod.tools.bpm_detector import detect_bpm

    # Create a dummy audio file so the path-existence check passes.
    dummy = tmp_path / "track.mp3"
    dummy.write_bytes(b"\x00" * 64)

    with patch("librosa.load", return_value=(np.zeros(22050), 22050)), \
         patch("librosa.beat.beat_track", return_value=(np.array([128.0]), None)):
        bpm = detect_bpm(str(dummy))

    assert isinstance(bpm, float)
    assert bpm == 128.0


def test_librosa_error_raises_runtime_error(tmp_path):
    """Errors from librosa are wrapped in RuntimeError."""
    from musicprod.tools.bpm_detector import detect_bpm

    dummy = tmp_path / "bad.mp3"
    dummy.write_bytes(b"\x00" * 64)

    with patch("librosa.load", side_effect=Exception("codec error")):
        with pytest.raises(RuntimeError, match="BPM detection failed"):
            detect_bpm(str(dummy))


def test_scalar_tempo_handled(tmp_path):
    """librosa returning a plain float (not ndarray) is handled correctly."""
    from musicprod.tools.bpm_detector import detect_bpm

    dummy = tmp_path / "track.mp3"
    dummy.write_bytes(b"\x00" * 64)

    with patch("librosa.load", return_value=(np.zeros(22050), 22050)), \
         patch("librosa.beat.beat_track", return_value=(120.0, None)):
        bpm = detect_bpm(str(dummy))

    assert bpm == 120.0
