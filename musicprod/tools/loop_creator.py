"""Tool 20 — Loop Creator.

Creates a seamless audio loop by repeating an audio file a given number
of times using pydub.
"""

from __future__ import annotations

from pathlib import Path


def create_loop(
    input_path: str,
    count: int = 4,
    crossfade: int = 0,
    output_path: str | None = None,
) -> Path:
    """Repeat *input_path* *count* times to create a loop file.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    count:
        Number of times to repeat the audio (default: 4).
        Must be >= 2.
    crossfade:
        Duration in milliseconds of the crossfade between repetitions
        (default: 0 = hard loop).  Must be >= 0.
    output_path:
        Optional destination path.  Defaults to ``<stem>_loop.<ext>``.

    Returns
    -------
    Path
        Path to the looped audio file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If *count* < 2 or *crossfade* < 0.
    RuntimeError
        If pydub / FFmpeg fails.
    """
    from pydub import AudioSegment  # lazy import

    if count < 2:
        raise ValueError(f"count must be >= 2, got {count}")
    if crossfade < 0:
        raise ValueError(f"crossfade must be >= 0, got {crossfade}")

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    try:
        audio = AudioSegment.from_file(str(src))
    except Exception as exc:
        raise RuntimeError(f"Failed to load audio: {exc}") from exc

    if crossfade > 0 and crossfade * 2 > len(audio):
        raise ValueError(
            f"crossfade ({crossfade} ms) is too large for the audio length ({len(audio)} ms)."
        )

    try:
        if crossfade > 0:
            result = audio
            for _ in range(count - 1):
                result = result.append(audio, crossfade=crossfade)
        else:
            result = audio * count
    except Exception as exc:
        raise RuntimeError(f"Loop creation failed: {exc}") from exc

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_loop{src.suffix}")

    # Ensure the destination always has a file extension so the exported
    # file is recognisable (e.g. song_loop.mp3, not just song_loop).
    if not dest.suffix:
        dest = dest.with_suffix(src.suffix or ".mp3")

    try:
        fmt = dest.suffix.lstrip(".") or "mp3"
        result.export(str(dest), format=fmt)
    except Exception as exc:
        raise RuntimeError(f"Failed to export loop audio: {exc}") from exc

    return dest
