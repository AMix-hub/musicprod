"""Tool 2 — BPM Detector.

Analyses an audio file and estimates its tempo in BPM using librosa.
"""

from __future__ import annotations

from pathlib import Path


def detect_bpm(file_path: str) -> float:
    """Estimate the tempo of an audio file in BPM.

    Parameters
    ----------
    file_path:
        Path to the audio file (MP3, WAV, FLAC, OGG, etc.).

    Returns
    -------
    float
        Estimated tempo in beats per minute.

    Raises
    ------
    FileNotFoundError
        If *file_path* does not exist.
    RuntimeError
        If librosa fails to analyse the file.
    """
    import librosa  # imported lazily — heavy dependency

    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    try:
        y, sr = librosa.load(str(path), sr=None, mono=True)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        # librosa >= 0.10 returns an ndarray; extract the scalar.
        bpm = float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo)
    except Exception as exc:
        raise RuntimeError(f"BPM detection failed: {exc}") from exc

    return round(bpm, 2)
