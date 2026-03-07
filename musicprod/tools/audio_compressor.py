"""Tool 19 — Audio Compressor.

Applies dynamic range compression to an audio file using pydub's
``compress_dynamic_range`` method.
"""

from __future__ import annotations

from pathlib import Path


def compress_audio(
    input_path: str,
    threshold: float = -20.0,
    ratio: float = 4.0,
    attack: float = 5.0,
    release: float = 50.0,
    output_path: str | None = None,
) -> Path:
    """Apply dynamic range compression to *input_path*.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    threshold:
        Threshold in dBFS above which compression is applied
        (default: -20.0).  Must be < 0.
    ratio:
        Compression ratio — e.g. ``4.0`` means 4:1 compression
        (default: 4.0).  Must be >= 1.0.
    attack:
        Attack time in milliseconds (default: 5.0).  Must be > 0.
    release:
        Release time in milliseconds (default: 50.0).  Must be > 0.
    output_path:
        Optional destination path.  Defaults to ``<stem>_compressed.<ext>``.

    Returns
    -------
    Path
        Path to the compressed audio file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If any parameter is out of range.
    RuntimeError
        If pydub / FFmpeg fails.
    """
    from pydub import AudioSegment  # lazy import
    from pydub.effects import compress_dynamic_range  # lazy import

    if threshold >= 0:
        raise ValueError(f"threshold must be < 0, got {threshold}")
    if ratio < 1.0:
        raise ValueError(f"ratio must be >= 1.0, got {ratio}")
    if attack <= 0:
        raise ValueError(f"attack must be > 0, got {attack}")
    if release <= 0:
        raise ValueError(f"release must be > 0, got {release}")

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    try:
        audio = AudioSegment.from_file(str(src))
    except Exception as exc:
        raise RuntimeError(f"Failed to load audio: {exc}") from exc

    try:
        compressed = compress_dynamic_range(
            audio,
            threshold=threshold,
            ratio=ratio,
            attack=attack,
            release=release,
        )
    except Exception as exc:
        raise RuntimeError(f"Compression failed: {exc}") from exc

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_compressed{src.suffix}")

    # Ensure the destination always has a file extension so the exported
    # file is recognisable (e.g. song_compressed.mp3, not just song_compressed).
    if not dest.suffix:
        dest = dest.with_suffix(src.suffix or ".mp3")

    try:
        fmt = dest.suffix.lstrip(".") or "mp3"
        compressed.export(str(dest), format=fmt)
    except Exception as exc:
        raise RuntimeError(f"Failed to export compressed audio: {exc}") from exc

    return dest
