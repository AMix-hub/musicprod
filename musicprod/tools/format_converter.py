"""Tool 3 — Audio Format Converter.

Converts audio files between common formats (MP3, WAV, FLAC, OGG, AAC …)
using pydub + FFmpeg.
"""

from __future__ import annotations

from pathlib import Path

SUPPORTED_FORMATS = {"mp3", "wav", "flac", "ogg", "aac", "m4a", "opus"}


def convert_format(
    input_path: str,
    target_format: str,
    output_path: str | None = None,
) -> Path:
    """Convert *input_path* to *target_format*.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    target_format:
        Desired output format, e.g. ``"mp3"``, ``"wav"``, ``"flac"``.
    output_path:
        Optional full destination path.  When *None* the output is saved
        next to the source file with the new extension.

    Returns
    -------
    Path
        Path to the converted file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If *target_format* is not supported.
    RuntimeError
        If pydub / FFmpeg fails to convert the file.
    """
    from pydub import AudioSegment  # lazy import

    fmt = target_format.lower().lstrip(".")
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format {fmt!r}. Supported: {sorted(SUPPORTED_FORMATS)}"
        )

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_suffix(f".{fmt}")

    try:
        audio = AudioSegment.from_file(str(src))
        audio.export(str(dest), format=fmt)
    except Exception as exc:
        raise RuntimeError(f"Format conversion failed: {exc}") from exc

    return dest
