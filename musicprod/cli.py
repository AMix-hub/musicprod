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
    Tools:
       1. youtube-to-mp3    Download audio from YouTube as MP3
       2. detect-bpm        Detect the BPM/tempo of an audio file
       3. convert-format    Convert audio between formats
       4. trim-audio        Trim an audio file to start/end timestamps
       5. edit-metadata     View or edit audio file metadata tags
       6. normalize-audio   Normalize loudness to a target dBFS
       7. shift-pitch       Shift the pitch by semitones
       8. split-audio       Split into equal-duration chunks
       9. merge-audio       Merge/concatenate multiple files into one
      10. plot-waveform     Generate a waveform PNG image
      --  hub               Launch the graphical MusicProd Hub
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


# ---------------------------------------------------------------------------
# Tool 6 — Audio Normalizer
# ---------------------------------------------------------------------------

@cli.command("normalize-audio")
@click.argument("input_path", metavar="FILE")
@click.option("--target-dbfs", default=-14.0, show_default=True, metavar="DBFS",
              help="Target loudness in dBFS (must be <= 0).")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Destination file path (default: <stem>_normalized.<ext>).")
def normalize_audio(input_path: str, target_dbfs: float, output: str | None) -> None:
    """Normalize the loudness of an audio file to a target dBFS level.

    \b
    Examples:
        musicprod normalize-audio track.mp3
        musicprod normalize-audio track.mp3 --target-dbfs -9.0
    """
    from musicprod.tools.audio_normalizer import normalize_audio as _normalize

    try:
        click.echo(f"Normalizing {input_path!r} to {target_dbfs} dBFS …")
        result = _normalize(input_path, target_dbfs=target_dbfs, output_path=output)
        click.secho(f"Saved: {result}", fg="green")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 7 — Pitch Shifter
# ---------------------------------------------------------------------------

@cli.command("shift-pitch")
@click.argument("input_path", metavar="FILE")
@click.option("--semitones", required=True, type=float, metavar="N",
              help="Semitones to shift (positive = higher, negative = lower).")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Destination file path (default: <stem>_pitched.<ext>).")
def shift_pitch(input_path: str, semitones: float, output: str | None) -> None:
    """Shift the pitch of an audio file by a number of semitones.

    \b
    Examples:
        musicprod shift-pitch track.mp3 --semitones 2
        musicprod shift-pitch track.mp3 --semitones -3 --output lower.mp3
    """
    from musicprod.tools.pitch_shifter import shift_pitch as _shift

    try:
        click.echo(f"Shifting pitch of {input_path!r} by {semitones:+.1f} semitones …")
        result = _shift(input_path, semitones=semitones, output_path=output)
        click.secho(f"Saved: {result}", fg="green")
    except (FileNotFoundError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 8 — Audio Splitter
# ---------------------------------------------------------------------------

@cli.command("split-audio")
@click.argument("input_path", metavar="FILE")
@click.option("--chunk-duration", required=True, type=float, metavar="SECONDS",
              help="Duration of each chunk in seconds.")
@click.option("--output-dir", "-o", default=None, metavar="DIR",
              help="Directory for output chunks (default: same as input).")
def split_audio(input_path: str, chunk_duration: float, output_dir: str | None) -> None:
    """Split an audio file into equal-duration chunks.

    \b
    Examples:
        musicprod split-audio long.mp3 --chunk-duration 30
        musicprod split-audio long.mp3 --chunk-duration 60 --output-dir ./chunks
    """
    from musicprod.tools.audio_splitter import split_audio as _split

    try:
        click.echo(f"Splitting {input_path!r} into {chunk_duration}s chunks …")
        chunks = _split(input_path, chunk_duration=chunk_duration, output_dir=output_dir)
        click.secho(f"Created {len(chunks)} chunk(s):", fg="green")
        for chunk in chunks:
            click.echo(f"  {chunk}")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 9 — Audio Merger
# ---------------------------------------------------------------------------

@cli.command("merge-audio")
@click.argument("input_paths", metavar="FILE", nargs=-1, required=True)
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Destination file path (default: merged.<ext> next to first input).")
def merge_audio(input_paths: tuple[str, ...], output: str | None) -> None:
    """Merge / concatenate multiple audio files into one.

    \b
    Example:
        musicprod merge-audio part1.mp3 part2.mp3 part3.mp3 --output full.mp3
    """
    from musicprod.tools.audio_merger import merge_audio as _merge

    try:
        click.echo(f"Merging {len(input_paths)} file(s) …")
        result = _merge(list(input_paths), output_path=output)
        click.secho(f"Saved: {result}", fg="green")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 10 — Waveform Plotter
# ---------------------------------------------------------------------------

@cli.command("plot-waveform")
@click.argument("input_path", metavar="FILE")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Destination PNG path (default: <stem>_waveform.png).")
@click.option("--width", default=12, show_default=True, type=int,
              help="Figure width in inches.")
@click.option("--height", default=4, show_default=True, type=int,
              help="Figure height in inches.")
def plot_waveform(input_path: str, output: str | None, width: int, height: int) -> None:
    """Generate a waveform PNG image for an audio file.

    \b
    Examples:
        musicprod plot-waveform track.mp3
        musicprod plot-waveform track.mp3 --width 16 --height 5 --output wave.png
    """
    from musicprod.tools.waveform_plotter import plot_waveform as _plot

    try:
        click.echo(f"Plotting waveform for {input_path!r} …")
        result = _plot(input_path, output_path=output, width=width, height=height)
        click.secho(f"Saved: {result}", fg="green")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Hub — launch the graphical interface
# ---------------------------------------------------------------------------

@cli.command("hub")
def hub() -> None:
    """Launch the MusicProd graphical hub (requires a display).

    \b
    Example:
        musicprod hub
    """
    try:
        from musicprod.hub import main
        main()
    except Exception as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)
