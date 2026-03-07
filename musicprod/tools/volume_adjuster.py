"""Tool 18 — Volume Adjuster.

Increases or decreases the volume of an audio file by a given number of
decibels using pydub.
"""

from __future__ import annotations

from pathlib import Path


def adjust_volume(
    input_path: str,
    db: float = 0.0,
    output_path: str | None = None,
) -> Path:
    """Adjust the volume of *input_path* by *db* decibels.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    db:
        Volume change in dB.  Positive values increase volume, negative
        values decrease it (default: 0.0 = no change).  Valid range:
        ``-60.0`` to ``+30.0``.
    output_path:
        Optional destination path.  Defaults to ``<stem>_volume.<ext>``.

    Returns
    -------
    Path
        Path to the adjusted audio file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If *db* is outside the allowed range.
    RuntimeError
        If pydub / FFmpeg fails.
    """
    from pydub import AudioSegment  # lazy import

    if not -60.0 <= db <= 30.0:
        raise ValueError(f"db must be between -60 and +30, got {db}")

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    try:
        audio = AudioSegment.from_file(str(src))
    except Exception as exc:
        raise RuntimeError(f"Failed to load audio: {exc}") from exc

    adjusted = audio + db

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_volume{src.suffix}")

    # Ensure the destination always has a file extension so the exported
    # file is recognisable (e.g. song_volume.mp3, not just song_volume).
    if not dest.suffix:
        dest = dest.with_suffix(src.suffix or ".mp3")

    try:
        fmt = dest.suffix.lstrip(".") or "mp3"
        adjusted.export(str(dest), format=fmt)
    except Exception as exc:
        raise RuntimeError(f"Failed to export audio: {exc}") from exc

    return dest
