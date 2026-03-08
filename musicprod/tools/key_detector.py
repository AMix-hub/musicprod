"""Tool 17 — Key Detector.

Detects the musical key (root + mode) of an audio file using librosa's
chromagram analysis and the Krumhansl-Schmuckler key-finding algorithm.

Enhancements over the basic version:
* Returns a ``confidence`` score (Pearson correlation, 0–1) along with
  the detected key so callers can assess reliability.
* Exposes a ``top_n`` parameter to get the *N* most likely keys ranked
  by score — useful when the key is ambiguous.
* Reports the relative major/minor counterpart automatically.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

# Krumhansl-Schmuckler key profiles
_MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
_MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Relative minor roots (natural minor relative to each major key root)
_RELATIVE_MINOR_OFFSET = 9  # A is the relative minor of C (9 semitones up)


class KeyResult(NamedTuple):
    """Result of key detection."""
    key: str
    """The detected key, e.g. ``"C major"`` or ``"A minor"``."""
    confidence: float
    """Pearson correlation coefficient (0–1); higher = more certain."""
    relative_key: str
    """The relative major/minor counterpart (e.g. ``"A minor"`` for ``"C major"``)."""


def detect_key(input_path: str, top_n: int = 1) -> str | list[KeyResult]:
    """Detect the musical key of *input_path*.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    top_n:
        When ``1`` (default), returns just the best key as a plain string
        for backward compatibility.  When > 1, returns a list of
        *top_n* :class:`KeyResult` named-tuples ranked by confidence.

    Returns
    -------
    str
        The detected key (e.g. ``"C major"``), when *top_n* == 1.
    list[KeyResult]
        Ranked list of *top_n* candidates, when *top_n* > 1.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    RuntimeError
        If librosa fails to process the file.
    ValueError
        If *top_n* < 1.
    """
    if top_n < 1:
        raise ValueError(f"top_n must be >= 1, got {top_n}")

    import numpy as np
    import librosa  # lazy import

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    try:
        y, sr = librosa.load(str(src), sr=None, mono=True)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)  # shape (12,)

        candidates: list[tuple[float, str, str]] = []  # (score, key, relative_key)

        for root in range(12):
            rotated = np.roll(chroma_mean, -root)
            maj_corr = float(np.corrcoef(rotated, _MAJOR_PROFILE)[0, 1])
            min_corr = float(np.corrcoef(rotated, _MINOR_PROFILE)[0, 1])

            # Relative key calculation
            rel_minor_root = (root + _RELATIVE_MINOR_OFFSET) % 12
            rel_major_root = (root - _RELATIVE_MINOR_OFFSET) % 12

            candidates.append((maj_corr, f"{_NOTES[root]} major",
                                f"{_NOTES[rel_minor_root]} minor"))
            candidates.append((min_corr, f"{_NOTES[root]} minor",
                                f"{_NOTES[rel_major_root]} major"))

        # Sort descending by correlation score
        candidates.sort(key=lambda c: c[0], reverse=True)

    except (FileNotFoundError, ValueError):
        raise
    except Exception as exc:
        raise RuntimeError(f"Key detection failed: {exc}") from exc

    if top_n == 1:
        # Backward-compatible: return plain string
        return candidates[0][1]

    results = [
        KeyResult(
            key=key,
            # Pearson correlation ranges from -1 to 1; negative values indicate
            # anti-correlation (the key does NOT match).  We clamp to 0 so that
            # confidence always represents "degree of match" (0 = no match / unclear,
            # 1 = perfect match).
            confidence=max(0.0, round(score, 4)),
            relative_key=rel_key,
        )
        for score, key, rel_key in candidates[:top_n]
    ]
    return results
