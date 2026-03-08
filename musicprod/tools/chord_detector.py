"""Tool 21 — Chord Detector.

Detects the chord progression of an audio file using chromagram analysis
and template matching against an extended set of chord types:

* 12 major triads (C, C#, …, B)
* 12 minor triads (Cm, C#m, …, Bm)
* 12 dominant 7th chords (C7, …, B7)
* 12 major 7th chords (Cmaj7, …, Bmaj7)
* 12 minor 7th chords (Cm7, …, Bm7)
* 12 diminished 7th chords (Cdim7, …, Bdim7)
* 12 suspended 2nd chords (Csus2, …, Bsus2)
* 12 suspended 4th chords (Csus4, …, Bsus4)

Total: 96 templates (up from the original 24).

Each returned segment now includes a ``confidence`` score (cosine
similarity, 0–1) so callers can filter out low-confidence detections.
"""

from __future__ import annotations

from pathlib import Path

# Chromatic pitch-class names
_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _build_chord_templates() -> tuple[list[str], "np.ndarray"]:  # noqa: F821
    """Return (chord_names, template_matrix) for all supported chord types.

    The template matrix has shape ``(n_chords, 12)``: one row per chord
    with 1s at the pitch classes that belong to the chord.
    """
    import numpy as np

    # Each entry: (suffix, intervals_above_root)
    chord_types = [
        ("",      (0, 4, 7)),           # major triad
        ("m",     (0, 3, 7)),           # minor triad
        ("7",     (0, 4, 7, 10)),       # dominant 7th
        ("maj7",  (0, 4, 7, 11)),       # major 7th
        ("m7",    (0, 3, 7, 10)),       # minor 7th
        ("dim7",  (0, 3, 6, 9)),        # diminished 7th (fully diminished)
        ("sus2",  (0, 2, 7)),           # suspended 2nd
        ("sus4",  (0, 5, 7)),           # suspended 4th
    ]

    names: list[str] = []
    rows: list[np.ndarray] = []
    for root in range(12):
        for suffix, intervals in chord_types:
            t = np.zeros(12)
            for iv in intervals:
                t[(root + iv) % 12] = 1
            names.append(f"{_NOTES[root]}{suffix}")
            rows.append(t)

    return names, np.array(rows)  # (n_chords, 12)


def detect_chords(
    input_path: str,
    hop_length: int = 4096,
    min_duration: float = 0.5,
    output_path: str | None = None,
) -> list[tuple[float, float, str, float]]:
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
    list of (start_seconds, end_seconds, chord_name, confidence) tuples
        ``confidence`` is the cosine similarity score (0–1) between the
        chromagram vector and the best-matching chord template.  A score
        below ~0.5 suggests ambiguous harmony.

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

    chord_names, templates = _build_chord_templates()  # (n_chords, 12)

    # Normalise each chroma frame to unit L2 norm (cosine similarity)
    chroma_norms = np.linalg.norm(chroma, axis=0, keepdims=True)
    chroma_norm = np.where(chroma_norms > 0, chroma / chroma_norms, chroma)

    # Normalise template rows to unit L2 norm
    row_norms = np.linalg.norm(templates, axis=1, keepdims=True)
    templates_norm = templates / np.where(row_norms > 0, row_norms, 1.0)

    # Cosine similarity: (n_chords, 12) @ (12, n_frames) → (n_chords, n_frames)
    scores = templates_norm @ chroma_norm  # shape (n_chords, n_frames)
    best_idx = np.argmax(scores, axis=0)   # (n_frames,)
    best_scores = scores[best_idx, np.arange(scores.shape[1])]  # (n_frames,)

    times = librosa.frames_to_time(
        np.arange(len(best_idx)), sr=sr, hop_length=hop_length
    )

    # Collect consecutive runs of the same chord into segments
    segments: list[tuple[float, float, str, float]] = []
    if len(best_idx) == 0:
        return segments

    seg_start = float(times[0])
    seg_chord = int(best_idx[0])
    seg_scores: list[float] = [float(best_scores[0])]

    for i in range(1, len(best_idx)):
        if int(best_idx[i]) != seg_chord:
            mean_conf = float(np.mean(seg_scores))
            segments.append((seg_start, float(times[i]), chord_names[seg_chord], mean_conf))
            seg_start = float(times[i])
            seg_chord = int(best_idx[i])
            seg_scores = [float(best_scores[i])]
        else:
            seg_scores.append(float(best_scores[i]))

    mean_conf = float(np.mean(seg_scores))
    segments.append((seg_start, float(times[-1]), chord_names[seg_chord], mean_conf))

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
    segments: list[tuple[float, float, str, float]],
    min_duration: float,
) -> list[tuple[float, float, str, float]]:
    """Merge segments shorter than *min_duration* into an adjacent segment."""
    changed = True
    while changed and len(segments) > 1:
        changed = False
        merged: list[tuple[float, float, str, float]] = []
        i = 0
        while i < len(segments):
            start, end, chord, conf = segments[i]
            if (end - start) < min_duration:
                changed = True
                if not merged:
                    if i + 1 < len(segments):
                        ns, ne, nc, nconf = segments[i + 1]
                        merged.append((start, ne, nc, nconf))
                        i += 2
                    else:
                        merged.append((start, end, chord, conf))
                        i += 1
                else:
                    ps, _, pc, pconf = merged[-1]
                    merged[-1] = (ps, end, pc, pconf)
                    i += 1
            else:
                merged.append((start, end, chord, conf))
                i += 1
        segments = merged
    return segments


# ---------------------------------------------------------------------------
# Formatting / output
# ---------------------------------------------------------------------------

def format_chords(segments: list[tuple[float, float, str, float]]) -> str:
    """Return a human-readable chord progression string.

    Each line has the form ``  M:SS – M:SS  Chord  (conf: 0.87)``.
    """
    lines = []
    for start, end, chord, conf in segments:
        lines.append(
            f"  {_fmt_time(start)} – {_fmt_time(end)}  {chord:<8}  (conf: {conf:.2f})"
        )
    return "\n".join(lines)


def _fmt_time(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 60}:{s % 60:02d}"


def _write_chords(
    segments: list[tuple[float, float, str, float]], output_path: str
) -> None:
    dst = Path(output_path).expanduser().resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w", encoding="utf-8") as fh:
        fh.write(format_chords(segments))
        fh.write("\n")
