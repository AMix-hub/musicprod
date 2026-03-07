"""Tool 1 — YouTube to MP3 converter.

Downloads audio from a YouTube URL and saves it as an MP3 file using yt-dlp.
FFmpeg must be installed and available on PATH.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import yt_dlp


def _sanitize_filename(name: str) -> str:
    """Remove characters that are unsafe in file names."""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()


def download_youtube_to_mp3(url: str, output_path: str | None = None) -> Path:
    """Download audio from *url* and convert it to MP3.

    Parameters
    ----------
    url:
        Full YouTube URL, e.g. ``https://www.youtube.com/watch?v=dQw4w9WgXcQ``.
    output_path:
        Optional destination file path (including ``.mp3`` extension).
        When *None* the file is saved in the current working directory using
        the video title as the filename.

    Returns
    -------
    Path
        Absolute path to the saved MP3 file.

    Raises
    ------
    ValueError
        If *url* is empty or does not look like a YouTube URL.
    RuntimeError
        If yt-dlp fails to download or convert the audio.
    """
    if not url or not url.strip():
        raise ValueError("URL must not be empty.")

    url = url.strip()
    if not re.search(r"(youtube\.com|youtu\.be)", url):
        raise ValueError(f"URL does not appear to be a YouTube URL: {url!r}")

    if output_path:
        dest = Path(output_path).expanduser().resolve()
        # Strip extension — yt-dlp appends it automatically.
        outtmpl = str(dest.with_suffix(""))
    else:
        outtmpl = "%(title)s"

    ydl_opts: dict = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        # Do not use --netrc-cmd to avoid the command-injection vector.
        "netrc": False,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
        except yt_dlp.utils.DownloadError as exc:
            raise RuntimeError(f"yt-dlp download failed: {exc}") from exc

    if output_path:
        result = Path(output_path).expanduser().resolve()
    else:
        title = _sanitize_filename(info.get("title", "audio"))
        result = Path(os.getcwd()) / f"{title}.mp3"

    return result
