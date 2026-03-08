"""Tests for musicprod.tools.chord_detector."""

from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# detect_chords
# ---------------------------------------------------------------------------

def test_file_not_found():
    from musicprod.tools.chord_detector import detect_chords

    with pytest.raises(FileNotFoundError, match="not found"):
        detect_chords("/non/existent/file.mp3")


def test_returns_list_of_tuples(tmp_path):
    """detect_chords returns a list of (start, end, chord, confidence) tuples."""
    from musicprod.tools.chord_detector import detect_chords

    dummy = tmp_path / "song.mp3"
    dummy.write_bytes(b"\x00" * 64)

    sr = 22050
    # 3-second mono signal at 22050 Hz — enough for a few chroma frames
    y = np.zeros(sr * 3)
    chroma = np.zeros((12, 10))
    # Make first 5 frames C-major-like (C=0, E=4, G=7)
    chroma[0, :5] = 1.0
    chroma[4, :5] = 1.0
    chroma[7, :5] = 1.0
    # Make last 5 frames Am-like (A=9, C=0, E=4)
    chroma[9, 5:] = 1.0
    chroma[0, 5:] = 1.0
    chroma[4, 5:] = 1.0

    fake_times = np.linspace(0.0, 3.0, 10)

    with patch("librosa.load", return_value=(y, sr)), \
         patch("librosa.feature.chroma_cqt", return_value=chroma), \
         patch("librosa.frames_to_time", return_value=fake_times):
        segments = detect_chords(str(dummy), hop_length=4096, min_duration=0.0)

    assert isinstance(segments, list)
    assert len(segments) >= 1
    for item in segments:
        assert len(item) == 4
        start, end, chord, conf = item
        assert isinstance(start, float)
        assert isinstance(end, float)
        assert isinstance(chord, str)
        assert isinstance(conf, float)
        assert 0.0 <= conf <= 1.0 + 1e-4  # allow floating-point rounding
        assert start <= end


def test_chord_names_are_valid(tmp_path):
    """All returned chord names are among the supported chord types."""
    from musicprod.tools.chord_detector import detect_chords, _build_chord_templates

    dummy = tmp_path / "song.mp3"
    dummy.write_bytes(b"\x00" * 64)

    # Build the full set of valid chord names from the current templates
    valid_names, _ = _build_chord_templates()
    valid_set = set(valid_names)

    sr = 22050
    y = np.zeros(sr * 2)
    chroma = np.eye(12)[:, :12]  # 12 frames, each dominated by one note class
    fake_times = np.linspace(0.0, 2.0, 12)

    with patch("librosa.load", return_value=(y, sr)), \
         patch("librosa.feature.chroma_cqt", return_value=chroma), \
         patch("librosa.frames_to_time", return_value=fake_times):
        segments = detect_chords(str(dummy), hop_length=4096, min_duration=0.0)

    for _, _, chord, _ in segments:
        assert chord in valid_set, f"Unexpected chord name: {chord!r}"


def test_librosa_error_raises_runtime_error(tmp_path):
    """Errors from librosa are wrapped in RuntimeError."""
    from musicprod.tools.chord_detector import detect_chords

    dummy = tmp_path / "bad.mp3"
    dummy.write_bytes(b"\x00" * 64)

    with patch("librosa.load", side_effect=Exception("codec error")):
        with pytest.raises(RuntimeError, match="Chord detection failed"):
            detect_chords(str(dummy))


def test_output_file_written(tmp_path):
    """When output_path is given the chord list is saved to a text file."""
    from musicprod.tools.chord_detector import detect_chords

    dummy = tmp_path / "song.mp3"
    dummy.write_bytes(b"\x00" * 64)
    out = tmp_path / "chords.txt"

    sr = 22050
    y = np.zeros(sr * 2)
    chroma = np.zeros((12, 6))
    chroma[0, :] = 1.0  # C dominant throughout
    chroma[4, :] = 1.0
    chroma[7, :] = 1.0
    fake_times = np.linspace(0.0, 2.0, 6)

    with patch("librosa.load", return_value=(y, sr)), \
         patch("librosa.feature.chroma_cqt", return_value=chroma), \
         patch("librosa.frames_to_time", return_value=fake_times):
        detect_chords(str(dummy), hop_length=4096, min_duration=0.0, output_path=str(out))

    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert len(content.strip()) > 0


def test_empty_audio_returns_empty_list(tmp_path):
    """Zero-length chroma (no frames) returns an empty list gracefully."""
    from musicprod.tools.chord_detector import detect_chords

    dummy = tmp_path / "silent.mp3"
    dummy.write_bytes(b"\x00" * 64)

    sr = 22050
    y = np.zeros(0)
    chroma = np.zeros((12, 0))
    fake_times = np.array([])

    with patch("librosa.load", return_value=(y, sr)), \
         patch("librosa.feature.chroma_cqt", return_value=chroma), \
         patch("librosa.frames_to_time", return_value=fake_times):
        segments = detect_chords(str(dummy), hop_length=4096, min_duration=0.0)

    assert segments == []


# ---------------------------------------------------------------------------
# _merge_short_segments
# ---------------------------------------------------------------------------

def test_merge_short_segments_removes_stub():
    """A segment shorter than min_duration is absorbed into its neighbour."""
    from musicprod.tools.chord_detector import _merge_short_segments

    segments = [
        (0.0, 2.0, "C", 0.9),
        (2.0, 2.3, "G", 0.6),   # short — 0.3 s < 0.5 s
        (2.3, 5.0, "Am", 0.8),
    ]
    merged = _merge_short_segments(segments, min_duration=0.5)

    # The 0.3-second G segment must be absorbed
    assert all((e - s) >= 0.5 for s, e, _, _conf in merged)
    assert len(merged) == 2


def test_merge_short_segments_single_segment():
    """A single-segment list is returned unchanged."""
    from musicprod.tools.chord_detector import _merge_short_segments

    segments = [(0.0, 1.0, "C", 0.9)]
    merged = _merge_short_segments(segments, min_duration=2.0)
    assert merged == [(0.0, 1.0, "C", 0.9)]


def test_merge_short_segments_all_long():
    """Segments that already meet min_duration are not changed."""
    from musicprod.tools.chord_detector import _merge_short_segments

    segments = [(0.0, 1.0, "C", 0.9), (1.0, 2.0, "G", 0.8), (2.0, 3.0, "Am", 0.7)]
    merged = _merge_short_segments(segments, min_duration=0.5)
    assert merged == segments


# ---------------------------------------------------------------------------
# format_chords / _fmt_time
# ---------------------------------------------------------------------------

def test_format_chords_output():
    """format_chords produces correctly formatted lines."""
    from musicprod.tools.chord_detector import format_chords

    segments = [
        (0.0, 4.0, "C", 0.95),
        (4.0, 8.0, "Am", 0.88),
        (8.0, 12.0, "F", 0.75),
    ]
    output = format_chords(segments)
    lines = output.splitlines()

    assert len(lines) == 3
    assert "0:00" in lines[0] and "C" in lines[0]
    assert "Am" in lines[1]
    assert "F" in lines[2]
    # Confidence scores should appear
    assert "conf" in lines[0]


def test_format_chords_time_format():
    """Times are formatted as M:SS (minutes:seconds zero-padded)."""
    from musicprod.tools.chord_detector import format_chords

    segments = [(65.0, 130.0, "G", 0.9)]
    output = format_chords(segments)

    assert "1:05" in output
    assert "2:10" in output


def test_format_chords_empty():
    """An empty segment list produces an empty string."""
    from musicprod.tools.chord_detector import format_chords

    assert format_chords([]) == ""


# ---------------------------------------------------------------------------
# _build_chord_templates
# ---------------------------------------------------------------------------

def test_build_chord_templates_shape():
    """Template matrix must be (96, 12) — 8 chord types × 12 roots."""
    from musicprod.tools.chord_detector import _build_chord_templates

    names, templates = _build_chord_templates()

    assert len(names) == 96
    assert templates.shape == (96, 12)


def test_build_chord_templates_c_major():
    """C major template should have 1s at indices 0 (C), 4 (E), 7 (G)."""
    from musicprod.tools.chord_detector import _build_chord_templates

    names, templates = _build_chord_templates()

    c_idx = names.index("C")
    row = templates[c_idx]
    assert row[0] == 1  # C
    assert row[4] == 1  # E
    assert row[7] == 1  # G
    assert row.sum() == 3


def test_build_chord_templates_a_minor():
    """Am template should have 1s at indices 9 (A), 0 (C), 4 (E)."""
    from musicprod.tools.chord_detector import _build_chord_templates

    names, templates = _build_chord_templates()

    am_idx = names.index("Am")
    row = templates[am_idx]
    assert row[9] == 1  # A
    assert row[0] == 1  # C
    assert row[4] == 1  # E
    assert row.sum() == 3


def test_build_chord_templates_c_dominant_7():
    """C7 template should have 1s at 0 (C), 4 (E), 7 (G), 10 (Bb)."""
    from musicprod.tools.chord_detector import _build_chord_templates

    names, templates = _build_chord_templates()

    c7_idx = names.index("C7")
    row = templates[c7_idx]
    assert row[0] == 1   # C
    assert row[4] == 1   # E
    assert row[7] == 1   # G
    assert row[10] == 1  # Bb
    assert row.sum() == 4


def test_build_chord_templates_includes_7th_and_sus_types():
    """All expected chord types should be present for the C root."""
    from musicprod.tools.chord_detector import _build_chord_templates

    names, _ = _build_chord_templates()
    name_set = set(names)

    for chord in ["C", "Cm", "C7", "Cmaj7", "Cm7", "Cdim7", "Csus2", "Csus4"]:
        assert chord in name_set, f"{chord!r} missing from templates"
