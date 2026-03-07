"""Tool 13 — Silence Remover.

Strips silent sections from an audio file using pydub's split-on-silence.
"""

from __future__ import annotations

from pathlib import Path


def remove_silence(
    input_path: str,
    min_silence_len: int = 500,
    silence_thresh: float = -40.0,
    padding: int = 100,
    output_path: str | None = None,
) -> Path:
    """Remove silent sections from *input_path*.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    min_silence_len:
        Minimum length of silence to remove, in milliseconds (default: 500).
        Must be > 0.
    silence_thresh:
        Audio is considered silent below this dBFS threshold (default: -40).
        Must be < 0.
    padding:
        Milliseconds of silence to keep around each non-silent chunk
        (default: 100).  Must be >= 0.
    output_path:
        Optional destination path.  Defaults to ``<stem>_trimmed.<ext>``.

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
    from pydub.silence import split_on_silence  # lazy import

    if min_silence_len <= 0:
        raise ValueError(f"min_silence_len must be > 0, got {min_silence_len}")
    if silence_thresh >= 0:
        raise ValueError(f"silence_thresh must be < 0, got {silence_thresh}")
    if padding < 0:
        raise ValueError(f"padding must be >= 0, got {padding}")

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    try:
        audio = AudioSegment.from_file(str(src))
    except Exception as exc:
        raise RuntimeError(f"Failed to load audio: {exc}") from exc

    chunks = split_on_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=padding,
    )

    if not chunks:
        raise RuntimeError("No non-silent audio segments found; try adjusting silence_thresh.")

    result = chunks[0]
    for chunk in chunks[1:]:
        result = result + chunk

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_nosilence{src.suffix}")

    # Ensure the destination always has a file extension so the exported
    # file is recognisable (e.g. song_nosilence.mp3, not just song_nosilence).
    if not dest.suffix:
        dest = dest.with_suffix(src.suffix or ".mp3")

    try:
        fmt = dest.suffix.lstrip(".") or "mp3"
        result.export(str(dest), format=fmt)
    except Exception as exc:
        raise RuntimeError(f"Failed to export audio: {exc}") from exc

    return dest
