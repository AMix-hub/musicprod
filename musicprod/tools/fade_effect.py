"""Tool 12 — Fade Effect.

Adds a fade-in and/or fade-out effect to an audio file using pydub.
"""

from __future__ import annotations

from pathlib import Path


def add_fade(
    input_path: str,
    fade_in: float = 0.0,
    fade_out: float = 0.0,
    output_path: str | None = None,
) -> Path:
    """Apply fade-in and/or fade-out to *input_path*.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    fade_in:
        Duration of the fade-in in seconds (default: 0 = no fade-in).
        Must be >= 0.
    fade_out:
        Duration of the fade-out in seconds (default: 0 = no fade-out).
        Must be >= 0.
    output_path:
        Optional destination path.  Defaults to ``<stem>_faded.<ext>``.

    Returns
    -------
    Path
        Path to the processed audio file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If *fade_in* or *fade_out* are negative, both are zero, or their
        combined duration exceeds the track length.
    RuntimeError
        If pydub / FFmpeg fails.
    """
    from pydub import AudioSegment  # lazy import

    if fade_in < 0:
        raise ValueError(f"fade_in must be >= 0, got {fade_in}")
    if fade_out < 0:
        raise ValueError(f"fade_out must be >= 0, got {fade_out}")
    if fade_in == 0 and fade_out == 0:
        raise ValueError("At least one of fade_in or fade_out must be > 0")

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    try:
        audio = AudioSegment.from_file(str(src))
    except Exception as exc:
        raise RuntimeError(f"Failed to load audio: {exc}") from exc

    duration_s = len(audio) / 1000.0
    if fade_in + fade_out > duration_s:
        raise ValueError(
            f"Combined fade duration ({fade_in + fade_out:.2f}s) exceeds "
            f"track length ({duration_s:.2f}s)"
        )

    if fade_in > 0:
        audio = audio.fade_in(int(fade_in * 1000))
    if fade_out > 0:
        audio = audio.fade_out(int(fade_out * 1000))

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_faded{src.suffix}")

    try:
        fmt = dest.suffix.lstrip(".") or "mp3"
        audio.export(str(dest), format=fmt)
    except Exception as exc:
        raise RuntimeError(f"Failed to export faded audio: {exc}") from exc

    return dest
