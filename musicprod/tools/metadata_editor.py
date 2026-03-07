"""Tool 5 — Metadata Editor.

View and edit audio file metadata tags (ID3, Vorbis comments, etc.)
using mutagen.  Supports MP3, FLAC, OGG, MP4/M4A and most other
formats that mutagen can handle.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

EDITABLE_TAGS = {"title", "artist", "album", "albumartist", "genre", "date", "tracknumber", "comment"}


def read_metadata(file_path: str) -> dict[str, Any]:
    """Return a dictionary of metadata tags from *file_path*.

    Parameters
    ----------
    file_path:
        Path to the audio file.

    Returns
    -------
    dict
        Mapping of tag name → value(s).

    Raises
    ------
    FileNotFoundError
        If *file_path* does not exist.
    RuntimeError
        If mutagen cannot read the file.
    """
    from mutagen import File as MutagenFile  # lazy import

    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    try:
        audio = MutagenFile(str(path), easy=True)
    except Exception as exc:
        raise RuntimeError(f"Failed to read metadata: {exc}") from exc

    if audio is None:
        raise RuntimeError(f"Unsupported or unreadable file: {path}")

    tags: dict[str, Any] = {}
    if audio.tags:
        for key, value in audio.tags.items():
            tags[key.lower()] = value[0] if len(value) == 1 else list(value)

    return tags


def write_metadata(
    file_path: str,
    *,
    title: str | None = None,
    artist: str | None = None,
    album: str | None = None,
    albumartist: str | None = None,
    genre: str | None = None,
    date: str | None = None,
    tracknumber: str | None = None,
    comment: str | None = None,
) -> dict[str, Any]:
    """Write metadata tags to *file_path* and return the updated tags.

    Only keyword arguments that are not *None* will be written; existing
    tags that are not mentioned are left untouched.

    Parameters
    ----------
    file_path:
        Path to the audio file.
    title, artist, album, albumartist, genre, date, tracknumber, comment:
        Tag values to set.

    Returns
    -------
    dict
        The full set of metadata tags after writing.

    Raises
    ------
    FileNotFoundError
        If *file_path* does not exist.
    RuntimeError
        If mutagen cannot open or save the file.
    """
    from mutagen import File as MutagenFile  # lazy import

    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    try:
        audio = MutagenFile(str(path), easy=True)
    except Exception as exc:
        raise RuntimeError(f"Failed to open file for writing: {exc}") from exc

    if audio is None:
        raise RuntimeError(f"Unsupported or unreadable file: {path}")

    if audio.tags is None:
        audio.add_tags()

    updates = {
        "title": title,
        "artist": artist,
        "album": album,
        "albumartist": albumartist,
        "genre": genre,
        "date": date,
        "tracknumber": tracknumber,
        "comment": comment,
    }
    for tag, value in updates.items():
        if value is not None:
            audio.tags[tag] = [value]

    try:
        audio.save()
    except Exception as exc:
        raise RuntimeError(f"Failed to save metadata: {exc}") from exc

    return read_metadata(file_path)
