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


def test_top_n_returns_list_of_bpm_results(tmp_path):
    """top_n > 1 returns a list of BpmResult named-tuples."""
    from musicprod.tools.bpm_detector import detect_bpm, BpmResult
    import numpy as np

    dummy = tmp_path / "track.mp3"
    dummy.write_bytes(b"\x00" * 64)

    onset_env = np.zeros(100)
    tempogram = np.eye(384, 100)  # mock tempogram
    tempo_axis = np.linspace(30, 300, 384)

    with patch("librosa.load", return_value=(np.zeros(22050), 22050)), \
         patch("librosa.onset.onset_strength", return_value=onset_env), \
         patch("librosa.feature.tempogram", return_value=tempogram), \
         patch("librosa.tempo_frequencies", return_value=tempo_axis), \
         patch("librosa.beat.beat_track", return_value=(np.array([128.0]), None)):
        results = detect_bpm(str(dummy), top_n=3)

    assert isinstance(results, list)
    assert len(results) == 3
    for r in results:
        assert isinstance(r, BpmResult)
        assert isinstance(r.bpm, float)
        assert 0.0 <= r.confidence <= 1.0


def test_top_n_1_still_returns_float(tmp_path):
    """top_n=1 returns a plain float for backward compatibility."""
    from musicprod.tools.bpm_detector import detect_bpm
    import numpy as np

    dummy = tmp_path / "track.mp3"
    dummy.write_bytes(b"\x00" * 64)

    with patch("librosa.load", return_value=(np.zeros(22050), 22050)), \
         patch("librosa.beat.beat_track", return_value=(np.array([120.0]), None)):
        result = detect_bpm(str(dummy), top_n=1)

    assert isinstance(result, float)


def test_top_n_zero_raises():
    """top_n < 1 raises ValueError."""
    from musicprod.tools.bpm_detector import detect_bpm
    with pytest.raises(ValueError, match="top_n"):
        detect_bpm("/fake.mp3", top_n=0)
