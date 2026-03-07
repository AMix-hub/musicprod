"""Tool 17 — Key Detector.

Detects the musical key (root + mode) of an audio file using librosa's
chromagram analysis and the Krumhansl-Schmuckler key-finding algorithm.
"""

from __future__ import annotations

from pathlib import Path

# Krumhansl-Schmuckler key profiles
_MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
_MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def detect_key(input_path: str) -> str:
    """Detect the musical key of *input_path*.

    Parameters
    ----------
    input_path:
        Path to the source audio file.

    Returns
    -------
    str
        The detected key, e.g. ``"C major"`` or ``"A minor"``.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    RuntimeError
        If librosa fails to process the file.
    """
    import numpy as np
    import librosa  # lazy import

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    try:
        y, sr = librosa.load(str(src), sr=None, mono=True)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)  # shape (12,)

        best_score = -float("inf")
        best_key = "C major"

        for root in range(12):
            rotated = np.roll(chroma_mean, -root)
            maj_score = float(np.corrcoef(rotated, _MAJOR_PROFILE)[0, 1])
            min_score = float(np.corrcoef(rotated, _MINOR_PROFILE)[0, 1])
            if maj_score > best_score:
                best_score = maj_score
                best_key = f"{_NOTES[root]} major"
            if min_score > best_score:
                best_score = min_score
                best_key = f"{_NOTES[root]} minor"

    except Exception as exc:
        raise RuntimeError(f"Key detection failed: {exc}") from exc

    return best_key
