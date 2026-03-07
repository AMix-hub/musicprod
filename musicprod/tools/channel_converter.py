"""Tool 14 — Channel Converter.

Converts an audio file between stereo and mono using pydub.
"""

from __future__ import annotations

from pathlib import Path

_VALID_CHANNELS = (1, 2)


def convert_channels(
    input_path: str,
    channels: int = 1,
    output_path: str | None = None,
) -> Path:
    """Convert the channel layout of *input_path*.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    channels:
        Target number of channels: ``1`` for mono, ``2`` for stereo
        (default: 1).
    output_path:
        Optional destination path.  Defaults to
        ``<stem>_mono.<ext>`` or ``<stem>_stereo.<ext>``.

    Returns
    -------
    Path
        Path to the converted file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If *channels* is not 1 or 2.
    RuntimeError
        If pydub / FFmpeg fails.
    """
    from pydub import AudioSegment  # lazy import

    if channels not in _VALID_CHANNELS:
        raise ValueError(f"channels must be 1 (mono) or 2 (stereo), got {channels}")

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    try:
        audio = AudioSegment.from_file(str(src))
    except Exception as exc:
        raise RuntimeError(f"Failed to load audio: {exc}") from exc

    converted = audio.set_channels(channels)

    suffix = "mono" if channels == 1 else "stereo"
    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_{suffix}{src.suffix}")

    # Ensure the destination always has a file extension so the exported
    # file is recognisable (e.g. song_mono.mp3, not just song_mono).
    if not dest.suffix:
        dest = dest.with_suffix(src.suffix or ".mp3")

    try:
        fmt = dest.suffix.lstrip(".") or "mp3"
        converted.export(str(dest), format=fmt)
    except Exception as exc:
        raise RuntimeError(f"Failed to export audio: {exc}") from exc

    return dest
