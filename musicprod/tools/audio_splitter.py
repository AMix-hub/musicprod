"""Tool 8 — Audio Splitter.

Splits an audio file into equal-duration chunks using pydub + FFmpeg.
"""

from __future__ import annotations

from pathlib import Path
from typing import List


def split_audio(
    input_path: str,
    chunk_duration: float,
    output_dir: str | None = None,
) -> List[Path]:
    """Split *input_path* into chunks of *chunk_duration* seconds.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    chunk_duration:
        Duration of each chunk in seconds.  Must be positive.
    output_dir:
        Optional directory for the output chunks.  Defaults to the same
        directory as the input file.

    Returns
    -------
    list[Path]
        Ordered list of paths to the generated chunk files.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If *chunk_duration* is not positive.
    RuntimeError
        If pydub / FFmpeg fails.
    """
    from pydub import AudioSegment  # lazy import

    if chunk_duration <= 0:
        raise ValueError(f"chunk_duration must be positive, got {chunk_duration}")

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    out_dir = Path(output_dir).expanduser().resolve() if output_dir else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        audio = AudioSegment.from_file(str(src))
    except Exception as exc:
        raise RuntimeError(f"Failed to load audio: {exc}") from exc

    chunk_ms = int(chunk_duration * 1000)
    duration_ms = len(audio)
    fmt = src.suffix.lstrip(".") or "mp3"

    chunks: List[Path] = []
    for i, start in enumerate(range(0, duration_ms, chunk_ms)):
        end = min(start + chunk_ms, duration_ms)
        chunk = audio[start:end]
        dest = out_dir / f"{src.stem}_part{i + 1:03d}{src.suffix}"
        try:
            chunk.export(str(dest), format=fmt)
        except Exception as exc:
            raise RuntimeError(f"Failed to export chunk {i + 1}: {exc}") from exc
        chunks.append(dest)

    return chunks
