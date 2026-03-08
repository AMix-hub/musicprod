"""Tool 22 — Vocal Auto-Tune.

Corrects the pitch of a vocal recording by snapping each detected note
to the nearest note in a chosen musical scale.  Uses PYIN for robust
fundamental-frequency estimation and librosa's phase-vocoder pitch
shifter for artefact-free correction.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Scale helpers
# ---------------------------------------------------------------------------

_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Flat-spelling → sharp-spelling aliases
_FLAT_MAP: dict[str, str] = {
    "Db": "C#", "Eb": "D#", "Fb": "E", "Gb": "F#",
    "Ab": "G#", "Bb": "A#", "Cb": "B",
}

_MAJOR_INTERVALS = (0, 2, 4, 5, 7, 9, 11)
_MINOR_INTERVALS = (0, 2, 3, 5, 7, 8, 10)   # natural minor


def _parse_scale(scale: str) -> list[int]:
    """Return the sorted pitch-class semitones (0–11) for *scale*.

    Accepted formats (case-insensitive):
        ``"chromatic"``                    — all 12 semitones
        ``"major"`` / ``"minor"``          — C major / C minor
        ``"C major"`` / ``"A minor"``
        ``"F# major"`` / ``"Bb minor"``

    Raises
    ------
    ValueError
        If the root note or mode cannot be recognised.
    """
    scale = scale.strip()
    parts = scale.lower().split()

    if len(parts) == 1 and parts[0] == "chromatic":
        return list(range(12))

    if len(parts) == 1:
        root_str, mode = "c", parts[0]
    else:
        root_str, mode = parts[0], parts[1]

    canon = root_str.capitalize()
    canon = _FLAT_MAP.get(canon, canon)
    if canon not in _NOTES:
        raise ValueError(
            f"Unknown root note {root_str!r}. "
            f"Use one of: {', '.join(_NOTES)} (or flat equivalents such as Bb, Eb)."
        )
    root = _NOTES.index(canon)

    if mode.startswith("maj"):
        intervals = _MAJOR_INTERVALS
    elif mode.startswith("min"):
        intervals = _MINOR_INTERVALS
    else:
        raise ValueError(
            f"Unknown mode {mode!r}. Use 'major', 'minor', or 'chromatic'."
        )
    return [(root + iv) % 12 for iv in intervals]


def _nearest_scale_midi(midi: float, scale_pcs: list[int]) -> float:
    """Return the MIDI pitch of the nearest note in *scale_pcs* to *midi*."""
    import numpy as np

    octave = int(midi) // 12
    # Span ±1 octave around the detected pitch to handle edge cases
    candidates = [
        (octave + oct_off) * 12 + pc
        for oct_off in (-1, 0, 1)
        for pc in scale_pcs
    ]
    arr = np.array(candidates, dtype=float)
    return float(arr[np.argmin(np.abs(arr - midi))])


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

# Output formats that soundfile can write natively
_SF_WRITE_FORMATS = {".wav", ".flac", ".ogg", ".aiff", ".aif"}


def autotune_vocals(
    input_path: str,
    scale: str = "chromatic",
    correction_strength: float = 1.0,
    output_path: str | None = None,
) -> Path:
    """Apply auto-tune pitch correction to a vocal recording.

    Each voiced segment is analysed with PYIN to find its median
    fundamental frequency.  The frequency is then snapped towards the
    nearest note in *scale* by *correction_strength* semitones and the
    segment is pitch-shifted accordingly.

    Parameters
    ----------
    input_path:
        Path to the source audio file (MP3, WAV, FLAC, OGG, etc.).
    scale:
        Target musical scale.  Examples: ``"chromatic"``,
        ``"C major"``, ``"A minor"``, ``"F# major"``, ``"Bb minor"``.
        Default: ``"chromatic"`` (snaps to the nearest semitone).
    correction_strength:
        How strongly to snap towards the target note.
        ``1.0`` = full correction (classic auto-tune effect).
        ``0.0`` = no correction.
        Values between 0 and 1 produce a subtle / natural effect.
        Must be in the range [0.0, 1.0].
    output_path:
        Optional destination path.  Defaults to
        ``<stem>_autotuned.<ext>``.  MP3 output falls back to ``.wav``
        because soundfile cannot write MP3.

    Returns
    -------
    Path
        Path to the pitch-corrected audio file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If *scale* cannot be parsed, or *correction_strength* is
        outside the valid range [0.0, 1.0].
    RuntimeError
        If audio processing fails.
    """
    import numpy as np
    import librosa          # lazy import — heavy dependency
    import soundfile as sf  # lazy import

    if not 0.0 <= correction_strength <= 1.0:
        raise ValueError(
            f"correction_strength must be between 0.0 and 1.0, "
            f"got {correction_strength}"
        )

    scale_pcs = _parse_scale(scale)  # raises ValueError on bad input

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_autotuned{src.suffix}")

    if not dest.suffix or dest.suffix.lower() not in _SF_WRITE_FORMATS:
        dest = dest.with_suffix(".wav")

    try:
        y, sr = librosa.load(str(src), sr=None, mono=True)

        if len(y) == 0:
            sf.write(str(dest), y, sr)
            return dest

        hop_length = 512

        # PYIN: probabilistic pitch estimator, robust for sustained vocals
        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=float(librosa.note_to_hz("C2")),
            fmax=float(librosa.note_to_hz("C7")),
            sr=sr,
            hop_length=hop_length,
        )

        y_out = y.copy()
        n_frames = len(f0)
        i = 0

        while i < n_frames:
            # Skip unvoiced / NaN frames
            if not voiced_flag[i] or np.isnan(f0[i]):
                i += 1
                continue

            # Collect a contiguous run of voiced frames
            seg_start_frame = i
            while i < n_frames and voiced_flag[i] and not np.isnan(f0[i]):
                i += 1
            seg_end_frame = i

            start_sample = seg_start_frame * hop_length
            end_sample = min(seg_end_frame * hop_length, len(y))
            if end_sample <= start_sample:
                continue

            segment = y[start_sample:end_sample]

            # Median pitch of the segment is more robust than the mean
            valid_f0 = f0[seg_start_frame:seg_end_frame]
            valid_f0 = valid_f0[~np.isnan(valid_f0)]
            if len(valid_f0) == 0 or float(np.median(valid_f0)) <= 0:
                continue

            median_f0 = float(np.median(valid_f0))
            detected_midi = float(librosa.hz_to_midi(median_f0))
            target_midi = _nearest_scale_midi(detected_midi, scale_pcs)
            shift = (target_midi - detected_midi) * correction_strength

            if abs(shift) < 0.01:
                continue  # negligible correction — leave as-is

            try:
                corrected = librosa.effects.pitch_shift(
                    segment, sr=sr, n_steps=shift
                )
                # Pad or trim to match original segment length
                if len(corrected) < len(segment):
                    corrected = np.pad(corrected, (0, len(segment) - len(corrected)))
                else:
                    corrected = corrected[: len(segment)]
                y_out[start_sample:end_sample] = corrected
            except Exception:
                pass  # leave this segment unmodified on failure

        sf.write(str(dest), y_out, sr)

    except (FileNotFoundError, ValueError):
        raise
    except Exception as exc:
        raise RuntimeError(f"Auto-tune failed: {exc}") from exc

    return dest
