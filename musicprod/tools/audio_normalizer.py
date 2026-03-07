"""Tool 6 — Audio Normalizer.

Normalizes the loudness of an audio file to a target dBFS level using pydub.
"""

from __future__ import annotations

from pathlib import Path


def normalize_audio(
    input_path: str,
    target_dbfs: float = -14.0,
    output_path: str | None = None,
) -> Path:
    """Normalize the loudness of *input_path* to *target_dbfs*.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    target_dbfs:
        Target loudness in dBFS (default: -14.0, a common streaming standard).
        Must be <= 0.
    output_path:
        Optional destination path.  Defaults to ``<stem>_normalized.<ext>``.

    Returns
    -------
    Path
        Path to the normalized file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If *target_dbfs* is greater than 0.
    RuntimeError
        If pydub / FFmpeg fails.
    """
    from pydub import AudioSegment  # lazy import

    if target_dbfs > 0:
        raise ValueError(f"target_dbfs must be <= 0, got {target_dbfs}")

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    try:
        audio = AudioSegment.from_file(str(src))
    except Exception as exc:
        raise RuntimeError(f"Failed to load audio: {exc}") from exc

    change_in_dbfs = target_dbfs - audio.dBFS
    normalized = audio.apply_gain(change_in_dbfs)

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_normalized{src.suffix}")

    # Ensure the destination always has a file extension so the exported
    # file is recognisable (e.g. song_normalized.mp3, not just song_normalized).
    if not dest.suffix:
        dest = dest.with_suffix(src.suffix or ".mp3")

    try:
        fmt = dest.suffix.lstrip(".") or "mp3"
        normalized.export(str(dest), format=fmt)
    except Exception as exc:
        raise RuntimeError(f"Failed to export normalized audio: {exc}") from exc

    return dest
