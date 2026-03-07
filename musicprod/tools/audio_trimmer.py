"""Tool 4 — Audio Trimmer.

Trims an audio file to a specific start/end time using pydub + FFmpeg.
Time values can be given as seconds (float/int) or as ``MM:SS`` / ``HH:MM:SS``
strings.
"""

from __future__ import annotations

import re
from pathlib import Path


def _parse_time(value: str | float | int) -> float:
    """Convert *value* to a number of seconds.

    Accepts:
    - A numeric value (int or float) already in seconds.
    - A string of the form ``"SS"``, ``"MM:SS"``, or ``"HH:MM:SS"``.
    """
    if isinstance(value, (int, float)):
        return float(value)

    value = str(value).strip()
    if re.fullmatch(r"\d+(\.\d+)?", value):
        return float(value)

    parts = value.split(":")
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

    raise ValueError(f"Unrecognised time format: {value!r}")


def trim_audio(
    input_path: str,
    start: str | float | int,
    end: str | float | int,
    output_path: str | None = None,
) -> Path:
    """Trim *input_path* from *start* to *end* and write the result.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    start:
        Start time as seconds or ``"MM:SS"`` / ``"HH:MM:SS"`` string.
    end:
        End time as seconds or ``"MM:SS"`` / ``"HH:MM:SS"`` string.
    output_path:
        Optional destination path.  Defaults to ``<stem>_trimmed.<ext>``.

    Returns
    -------
    Path
        Path to the trimmed file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If *start* >= *end* or either time exceeds the file duration.
    RuntimeError
        If pydub / FFmpeg fails.
    """
    from pydub import AudioSegment  # lazy import

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    start_ms = int(_parse_time(start) * 1000)
    end_ms = int(_parse_time(end) * 1000)

    if start_ms >= end_ms:
        raise ValueError(
            f"Start time ({start}) must be less than end time ({end})."
        )

    try:
        audio = AudioSegment.from_file(str(src))
    except Exception as exc:
        raise RuntimeError(f"Failed to load audio: {exc}") from exc

    duration_ms = len(audio)
    if end_ms > duration_ms:
        raise ValueError(
            f"End time {end_ms / 1000:.2f}s exceeds file duration "
            f"{duration_ms / 1000:.2f}s."
        )

    trimmed = audio[start_ms:end_ms]

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_trimmed{src.suffix}")

    try:
        fmt = dest.suffix.lstrip(".") or "mp3"
        trimmed.export(str(dest), format=fmt)
    except Exception as exc:
        raise RuntimeError(f"Failed to export trimmed audio: {exc}") from exc

    return dest
