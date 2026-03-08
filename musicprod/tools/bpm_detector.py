"""Tool 2 — BPM Detector.

Analyses an audio file and estimates its tempo in BPM using librosa.

Enhancements over the basic version:
* Returns a ``confidence`` score alongside the BPM by examining the
  strength of the dominant beat-period peak in the tempo gram.
* Exposes a ``top_n`` parameter: when > 1, returns the *N* most likely
  tempos (useful for ambiguous tracks where the "half-time" reading is
  equally valid).
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple


class BpmResult(NamedTuple):
    """Result of BPM detection."""
    bpm: float
    """Estimated tempo in beats per minute."""
    confidence: float
    """Relative strength of the dominant beat-period peak (0–1)."""


def detect_bpm(file_path: str, top_n: int = 1) -> float | list[BpmResult]:
    """Estimate the tempo of an audio file in BPM.

    Parameters
    ----------
    file_path:
        Path to the audio file (MP3, WAV, FLAC, OGG, etc.).
    top_n:
        When ``1`` (default), returns just the best BPM as a plain
        ``float`` for backward compatibility.  When > 1, returns a list
        of *top_n* :class:`BpmResult` named-tuples ranked by confidence.

    Returns
    -------
    float
        Estimated tempo in BPM, when *top_n* == 1.
    list[BpmResult]
        Ranked list of *top_n* BPM candidates, when *top_n* > 1.

    Raises
    ------
    FileNotFoundError
        If *file_path* does not exist.
    ValueError
        If *top_n* < 1.
    RuntimeError
        If librosa fails to analyse the file.
    """
    if top_n < 1:
        raise ValueError(f"top_n must be >= 1, got {top_n}")

    import numpy as np
    import librosa  # imported lazily — heavy dependency

    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    try:
        y, sr = librosa.load(str(path), sr=None, mono=True)

        # Onset strength envelope — used for beat tracking and tempo analysis
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)

        # Tempogram: per-frame estimate of the auto-correlation of the
        # onset envelope (rows = BPM candidates, cols = time frames)
        tempogram = librosa.feature.tempogram(onset_envelope=onset_env, sr=sr)
        # Aggregate over time to get a global tempo histogram
        tempo_hist = np.mean(tempogram, axis=1)  # shape: (n_bpm_candidates,)
        tempo_axis = librosa.tempo_frequencies(len(tempo_hist), sr=sr)

        # Normalise histogram to [0, 1]
        hist_max = tempo_hist.max()
        if hist_max > 0:
            tempo_hist = tempo_hist / hist_max

        # Sort candidates by descending strength
        order = np.argsort(tempo_hist)[::-1]
        top_bpms = tempo_axis[order[:top_n]]
        top_confs = tempo_hist[order[:top_n]]

        # Primary BPM via beat_track (more accurate than peak of tempogram)
        primary_tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        primary_bpm = float(primary_tempo[0]) if hasattr(primary_tempo, "__len__") else float(primary_tempo)

    except (FileNotFoundError, ValueError):
        raise
    except Exception as exc:
        raise RuntimeError(f"BPM detection failed: {exc}") from exc

    if top_n == 1:
        return round(primary_bpm, 2)

    # Replace the top candidate with the more-accurate beat_track value
    results = [
        BpmResult(bpm=round(float(b), 2), confidence=round(float(c), 4))
        for b, c in zip(top_bpms, top_confs)
    ]
    results[0] = BpmResult(bpm=round(primary_bpm, 2), confidence=results[0].confidence)
    return results
