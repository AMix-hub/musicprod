"""MusicProd CLI — entry point for all music production tools."""

from __future__ import annotations

import sys

import click


# ---------------------------------------------------------------------------
# Top-level group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(package_name="musicprod")
def cli() -> None:
    """MusicProd — music production tools.

    \b
    Top 5 tools:
      1. youtube-to-mp3   Download audio from YouTube as MP3
      2. detect-bpm       Detect the BPM/tempo of an audio file
      3. convert-format   Convert audio between formats
      4. trim-audio       Trim an audio file to start/end timestamps
      5. edit-metadata    View or edit audio file metadata tags
    """


# ---------------------------------------------------------------------------
# Tool 1 — YouTube → MP3
# ---------------------------------------------------------------------------

@cli.command("youtube-to-mp3")
@click.argument("url")
@click.option(
    "--output",
    "-o",
    default=None,
    metavar="FILE",
    help="Destination MP3 file path (default: <title>.mp3 in current directory).",
)
def youtube_to_mp3(url: str, output: str | None) -> None:
    """Download audio from a YouTube URL and save it as an MP3 file.

    \b
    Example:
        musicprod youtube-to-mp3 "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    """
    from musicprod.tools.youtube_to_mp3 import download_youtube_to_mp3

    try:
        click.echo(f"Downloading: {url}")
        result = download_youtube_to_mp3(url, output_path=output)
        click.secho(f"Saved: {result}", fg="green")
    except (ValueError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 2 — BPM Detector
# ---------------------------------------------------------------------------

@cli.command("detect-bpm")
@click.argument("file_path", metavar="FILE")
def detect_bpm(file_path: str) -> None:
    """Estimate the BPM/tempo of an audio file.

    \b
    Example:
        musicprod detect-bpm track.mp3
    """
    from musicprod.tools.bpm_detector import detect_bpm as _detect

    try:
        click.echo(f"Analysing: {file_path}")
        bpm = _detect(file_path)
        click.secho(f"Detected BPM: {bpm}", fg="green")
    except (FileNotFoundError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 3 — Audio Format Converter
# ---------------------------------------------------------------------------

@cli.command("convert-format")
@click.argument("input_path", metavar="FILE")
@click.option("--to", "target_format", required=True, metavar="FORMAT",
              help="Target format, e.g. mp3, wav, flac, ogg.")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Destination file path.")
def convert_format(input_path: str, target_format: str, output: str | None) -> None:
    """Convert an audio file to a different format.

    \b
    Example:
        musicprod convert-format recording.wav --to mp3
    """
    from musicprod.tools.format_converter import convert_format as _convert

    try:
        click.echo(f"Converting {input_path!r} → {target_format.upper()} …")
        result = _convert(input_path, target_format, output_path=output)
        click.secho(f"Saved: {result}", fg="green")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 4 — Audio Trimmer
# ---------------------------------------------------------------------------

@cli.command("trim-audio")
@click.argument("input_path", metavar="FILE")
@click.option("--start", required=True, metavar="TIME",
              help="Start time in seconds or MM:SS / HH:MM:SS.")
@click.option("--end", required=True, metavar="TIME",
              help="End time in seconds or MM:SS / HH:MM:SS.")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Destination file path (default: <stem>_trimmed.<ext>).")
def trim_audio(input_path: str, start: str, end: str, output: str | None) -> None:
    """Trim an audio file to a start/end timestamp.

    TIME can be given as seconds (e.g. 30, 90.5) or as MM:SS / HH:MM:SS.

    \b
    Examples:
        musicprod trim-audio song.mp3 --start 0:30 --end 1:45
        musicprod trim-audio song.mp3 --start 10 --end 70 --output short.mp3
    """
    from musicprod.tools.audio_trimmer import trim_audio as _trim

    try:
        click.echo(f"Trimming {input_path!r} from {start} to {end} …")
        result = _trim(input_path, start, end, output_path=output)
        click.secho(f"Saved: {result}", fg="green")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 5 — Metadata Editor
# ---------------------------------------------------------------------------

@cli.group("edit-metadata")
def edit_metadata() -> None:
    """View or edit audio file metadata tags (ID3, Vorbis, …)."""


@edit_metadata.command("view")
@click.argument("file_path", metavar="FILE")
def metadata_view(file_path: str) -> None:
    """Display all metadata tags of FILE.

    \b
    Example:
        musicprod edit-metadata view track.mp3
    """
    from musicprod.tools.metadata_editor import read_metadata

    try:
        tags = read_metadata(file_path)
        if not tags:
            click.echo("No metadata tags found.")
        else:
            for key, value in sorted(tags.items()):
                click.echo(f"  {key:<16} {value}")
    except (FileNotFoundError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


@edit_metadata.command("set")
@click.argument("file_path", metavar="FILE")
@click.option("--title", default=None, help="Track title.")
@click.option("--artist", default=None, help="Artist name.")
@click.option("--album", default=None, help="Album name.")
@click.option("--albumartist", default=None, help="Album artist.")
@click.option("--genre", default=None, help="Genre.")
@click.option("--date", default=None, help="Release date / year.")
@click.option("--tracknumber", default=None, help="Track number.")
@click.option("--comment", default=None, help="Comment.")
def metadata_set(
    file_path: str,
    title: str | None,
    artist: str | None,
    album: str | None,
    albumartist: str | None,
    genre: str | None,
    date: str | None,
    tracknumber: str | None,
    comment: str | None,
) -> None:
    """Set one or more metadata tags on FILE.

    \b
    Example:
        musicprod edit-metadata set track.mp3 --title "My Song" --artist "DJ X"
    """
    from musicprod.tools.metadata_editor import write_metadata

    try:
        tags = write_metadata(
            file_path,
            title=title,
            artist=artist,
            album=album,
            albumartist=albumartist,
            genre=genre,
            date=date,
            tracknumber=tracknumber,
            comment=comment,
        )
        click.secho("Metadata updated:", fg="green")
        for key, value in sorted(tags.items()):
            click.echo(f"  {key:<16} {value}")
    except (FileNotFoundError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)
