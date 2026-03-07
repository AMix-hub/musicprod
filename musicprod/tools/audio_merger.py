"""Tool 9 — Audio Merger.

Concatenates multiple audio files into a single file using pydub + FFmpeg.
"""

from __future__ import annotations

from pathlib import Path
from typing import List


def merge_audio(
    input_paths: List[str],
    output_path: str | None = None,
) -> Path:
    """Merge *input_paths* into a single audio file.

    Files are concatenated in the order provided.

    Parameters
    ----------
    input_paths:
        Ordered list of paths to source audio files.  At least two files
        must be supplied.
    output_path:
        Optional destination path.  Defaults to ``merged.<ext>`` in the
        directory of the first input file, where ``<ext>`` is that file's
        extension.

    Returns
    -------
    Path
        Path to the merged file.

    Raises
    ------
    FileNotFoundError
        If any file in *input_paths* does not exist.
    ValueError
        If fewer than two files are provided.
    RuntimeError
        If pydub / FFmpeg fails.
    """
    from pydub import AudioSegment  # lazy import

    if len(input_paths) < 2:
        raise ValueError("At least two input files are required to merge.")

    paths: List[Path] = []
    for p in input_paths:
        resolved = Path(p).expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Input file not found: {resolved}")
        paths.append(resolved)

    try:
        combined = AudioSegment.from_file(str(paths[0]))
        for path in paths[1:]:
            segment = AudioSegment.from_file(str(path))
            combined = combined + segment
    except Exception as exc:
        raise RuntimeError(f"Failed to merge audio: {exc}") from exc

    first = paths[0]
    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = first.parent / f"merged{first.suffix}"

    try:
        fmt = dest.suffix.lstrip(".") or "mp3"
        combined.export(str(dest), format=fmt)
    except Exception as exc:
        raise RuntimeError(f"Failed to export merged audio: {exc}") from exc

    return dest
