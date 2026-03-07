"""Tool 16 — Reverb Effect.

Adds a simple algorithmic reverb to an audio file by layering delayed,
decayed copies of the signal using pydub.
"""

from __future__ import annotations

from pathlib import Path


def add_reverb(
    input_path: str,
    delay_ms: int = 80,
    decay: float = 0.4,
    reflections: int = 5,
    output_path: str | None = None,
) -> Path:
    """Add a reverb effect to *input_path*.

    A simple room-reverb simulation is produced by overlaying several
    progressively quieter and delayed copies of the source signal.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    delay_ms:
        Delay between each reflection in milliseconds (default: 80).
        Must be > 0.
    decay:
        Volume reduction factor per reflection, between 0 and 1
        (default: 0.4).  Lower = darker, more distant reverb.
    reflections:
        Number of reflected copies to add (default: 5, range 1–20).
    output_path:
        Optional destination path.  Defaults to ``<stem>_reverb.<ext>``.

    Returns
    -------
    Path
        Path to the processed audio file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If parameters are out of range.
    RuntimeError
        If pydub / FFmpeg fails.
    """
    from pydub import AudioSegment  # lazy import

    if delay_ms <= 0:
        raise ValueError(f"delay_ms must be > 0, got {delay_ms}")
    if not 0 < decay < 1:
        raise ValueError(f"decay must be between 0 and 1 (exclusive), got {decay}")
    if not 1 <= reflections <= 20:
        raise ValueError(f"reflections must be between 1 and 20, got {reflections}")

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    try:
        audio = AudioSegment.from_file(str(src))
    except Exception as exc:
        raise RuntimeError(f"Failed to load audio: {exc}") from exc

    # Build a wet signal by layering echoes
    total_delay = delay_ms * reflections
    wet = AudioSegment.silent(duration=len(audio) + total_delay,
                               frame_rate=audio.frame_rate).set_channels(audio.channels)

    for i in range(1, reflections + 1):
        gain_db = 20 * _log10_safe(decay ** i)
        offset = delay_ms * i
        reflection = audio - abs(gain_db)  # attenuate
        wet = wet.overlay(reflection, position=offset)

    # Mix dry + wet
    dry_extended = audio + AudioSegment.silent(duration=total_delay,
                                                frame_rate=audio.frame_rate).set_channels(audio.channels)
    mixed = dry_extended.overlay(wet)

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_reverb{src.suffix}")

    # Ensure the destination always has a file extension so the exported
    # file is recognisable (e.g. song_reverb.mp3, not just song_reverb).
    if not dest.suffix:
        dest = dest.with_suffix(src.suffix or ".mp3")

    try:
        fmt = dest.suffix.lstrip(".") or "mp3"
        mixed.export(str(dest), format=fmt)
    except Exception as exc:
        raise RuntimeError(f"Failed to export reverb audio: {exc}") from exc

    return dest


def _log10_safe(x: float) -> float:
    import math
    return math.log10(max(x, 1e-9))
