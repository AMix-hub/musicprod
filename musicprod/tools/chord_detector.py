"""Tool 21 — Chord Detector.

Detects the chord progression of an audio file using chromagram analysis
and template matching against 24 major/minor triad templates.
"""

from __future__ import annotations

from pathlib import Path

# Chromatic pitch-class names
_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _build_chord_templates() -> tuple[list[str], "np.ndarray"]:  # noqa: F821
    """Return (chord_names, template_matrix) for 24 major/minor triads.

    The template matrix has shape ``(24, 12)``: one binary row per chord
    with 1s at the pitch classes that belong to the triad.
    """
    import numpy as np

    names: list[str] = []
    rows: list[np.ndarray] = []
    for root in range(12):
        # Major triad: root + major 3rd (+4) + perfect 5th (+7)
        t = np.zeros(12)
        t[root] = 1
        t[(root + 4) % 12] = 1
        t[(root + 7) % 12] = 1
        names.append(_NOTES[root])
        rows.append(t)

        # Minor triad: root + minor 3rd (+3) + perfect 5th (+7)
        t = np.zeros(12)
        t[root] = 1
        t[(root + 3) % 12] = 1
        t[(root + 7) % 12] = 1
        names.append(f"{_NOTES[root]}m")
        rows.append(t)

    return names, np.array(rows)  # (24, 12)


def detect_chords(
    input_path: str,
    hop_length: int = 4096,
    min_duration: float = 0.5,
    output_path: str | None = None,
) -> list[tuple[float, float, str]]:
    """Detect the chord progression of an audio file.

    Parameters
    ----------
    input_path:
        Path to the source audio file (MP3, WAV, FLAC, OGG, etc.).
    hop_length:
        Number of audio samples between successive chromagram frames.
        Larger values produce coarser but smoother chord boundaries.
        Default: 4096 (~93 ms at 44.1 kHz).
    min_duration:
        Minimum chord segment length in seconds.  Segments shorter than
        this are merged into their neighbour to reduce noise.
        Default: 0.5 s.
    output_path:
        Optional path for a plain-text file that receives the formatted
        chord list.  The directory is created automatically if needed.

    Returns
    -------
    list of (start_seconds, end_seconds, chord_name) tuples, sorted by
    start time.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    RuntimeError
        If librosa fails to process the file.
    """
    import numpy as np
    import librosa  # lazy import — heavy dependency

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    try:
        y, sr = librosa.load(str(src), sr=None, mono=True)
        # CQT-based chroma is more robust to timbre than STFT chroma
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
        # shape: (12, n_frames)
    except Exception as exc:
        raise RuntimeError(f"Chord detection failed: {exc}") from exc

    chord_names, templates = _build_chord_templates()  # (24, 12)

    # Normalise each chroma frame to sum = 1
    col_sums = chroma.sum(axis=0, keepdims=True)
    chroma_norm = np.where(col_sums > 0, chroma / col_sums, chroma)

    # Normalise template rows to unit L2 norm (cosine similarity via dot)
    row_norms = np.linalg.norm(templates, axis=1, keepdims=True)
    templates_norm = templates / np.where(row_norms > 0, row_norms, 1.0)

    # Similarity score: (24, 12) @ (12, n_frames) → (24, n_frames)
    scores = templates_norm @ chroma_norm
    best_idx = np.argmax(scores, axis=0)  # (n_frames,)

    times = librosa.frames_to_time(
        np.arange(len(best_idx)), sr=sr, hop_length=hop_length
    )

    # Collect consecutive runs of the same chord into segments
    segments: list[tuple[float, float, str]] = []
    if len(best_idx) == 0:
        return segments

    seg_start = float(times[0])
    seg_chord = int(best_idx[0])

    for i in range(1, len(best_idx)):
        if int(best_idx[i]) != seg_chord:
            segments.append((seg_start, float(times[i]), chord_names[seg_chord]))
            seg_start = float(times[i])
            seg_chord = int(best_idx[i])
    segments.append((seg_start, float(times[-1]), chord_names[seg_chord]))

    # Merge very short segments to reduce noise
    if min_duration > 0 and len(segments) > 1:
        segments = _merge_short_segments(segments, min_duration)

    if output_path is not None:
        _write_chords(segments, output_path)

    return segments


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _merge_short_segments(
    segments: list[tuple[float, float, str]],
    min_duration: float,
) -> list[tuple[float, float, str]]:
    """Merge segments shorter than *min_duration* into an adjacent segment."""
    changed = True
    while changed and len(segments) > 1:
        changed = False
        merged: list[tuple[float, float, str]] = []
        i = 0
        while i < len(segments):
            start, end, chord = segments[i]
            if (end - start) < min_duration:
                changed = True
                if not merged:
                    # Absorb this stub into the next segment
                    if i + 1 < len(segments):
                        ns, ne, nc = segments[i + 1]
                        merged.append((start, ne, nc))
                        i += 2
                    else:
                        merged.append((start, end, chord))
                        i += 1
                else:
                    # Absorb into the previous segment
                    ps, _, pc = merged[-1]
                    merged[-1] = (ps, end, pc)
                    i += 1
            else:
                merged.append((start, end, chord))
                i += 1
        segments = merged
    return segments


# ---------------------------------------------------------------------------
# Formatting / output
# ---------------------------------------------------------------------------

def format_chords(segments: list[tuple[float, float, str]]) -> str:
    """Return a human-readable chord progression string.

    Each line has the form ``  M:SS – M:SS  Chord``.
    """
    lines = []
    for start, end, chord in segments:
        lines.append(f"  {_fmt_time(start)} – {_fmt_time(end)}  {chord}")
    return "\n".join(lines)


def _fmt_time(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 60}:{s % 60:02d}"


def _write_chords(segments: list[tuple[float, float, str]], output_path: str) -> None:
    dst = Path(output_path).expanduser().resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w", encoding="utf-8") as fh:
        fh.write(format_chords(segments))
        fh.write("\n")
