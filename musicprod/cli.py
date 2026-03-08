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
      11. reduce-noise      Reduce background noise via spectral subtraction
      12. add-fade          Add fade-in / fade-out to an audio file
      13. remove-silence    Strip silent sections from an audio file
      14. convert-channels  Convert between stereo and mono
      15. change-tempo      Change playback speed without altering pitch
      16. add-reverb        Add a reverb effect to an audio file
      17. detect-key        Detect the musical key of an audio file
      18. adjust-volume     Increase or decrease volume by dB
      19. compress-audio    Apply dynamic range compression
      20. create-loop       Repeat audio N times to create a loop
      21. detect-chords     Detect the chord progression of an audio file
      --  hub               Launch the graphical MusicProd Hub
      --  update            Update to the latest version from main
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
# Tool 11 — Noise Reducer
# ---------------------------------------------------------------------------

@cli.command("reduce-noise")
@click.argument("input_path", metavar="FILE")
@click.option("--noise-duration", default=0.5, show_default=True, type=float, metavar="SECONDS",
              help="Seconds at the start of the file used to estimate noise profile.")
@click.option("--strength", default=1.0, show_default=True, type=float, metavar="FACTOR",
              help="Subtraction strength (0–3, default 1.0).")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Destination file path (default: <stem>_denoised.<ext>).")
def reduce_noise(input_path: str, noise_duration: float, strength: float, output: str | None) -> None:
    """Reduce background noise using spectral subtraction.

    \b
    Examples:
        musicprod reduce-noise noisy.wav
        musicprod reduce-noise noisy.wav --strength 1.5 --noise-duration 1.0
    """
    from musicprod.tools.noise_reducer import reduce_noise as _reduce

    try:
        click.echo(f"Reducing noise in {input_path!r} …")
        result = _reduce(input_path, noise_duration=noise_duration, strength=strength,
                         output_path=output)
        click.secho(f"Saved: {result}", fg="green")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 12 — Fade Effect
# ---------------------------------------------------------------------------

@cli.command("add-fade")
@click.argument("input_path", metavar="FILE")
@click.option("--fade-in", default=0.0, show_default=True, type=float, metavar="SECONDS",
              help="Fade-in duration in seconds (0 = no fade-in).")
@click.option("--fade-out", default=0.0, show_default=True, type=float, metavar="SECONDS",
              help="Fade-out duration in seconds (0 = no fade-out).")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Destination file path (default: <stem>_faded.<ext>).")
def add_fade(input_path: str, fade_in: float, fade_out: float, output: str | None) -> None:
    """Add fade-in and/or fade-out to an audio file.

    \b
    Examples:
        musicprod add-fade track.mp3 --fade-in 2.0 --fade-out 3.0
        musicprod add-fade track.mp3 --fade-out 5.0
    """
    from musicprod.tools.fade_effect import add_fade as _fade

    try:
        click.echo(f"Adding fade to {input_path!r} (in={fade_in}s, out={fade_out}s) …")
        result = _fade(input_path, fade_in=fade_in, fade_out=fade_out, output_path=output)
        click.secho(f"Saved: {result}", fg="green")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 13 — Silence Remover
# ---------------------------------------------------------------------------

@cli.command("remove-silence")
@click.argument("input_path", metavar="FILE")
@click.option("--min-silence-len", default=500, show_default=True, type=int, metavar="MS",
              help="Minimum silence length to remove (ms).")
@click.option("--silence-thresh", default=-40.0, show_default=True, type=float, metavar="DBFS",
              help="Silence threshold in dBFS.")
@click.option("--padding", default=100, show_default=True, type=int, metavar="MS",
              help="Milliseconds of silence to keep around each chunk.")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Destination file path (default: <stem>_nosilence.<ext>).")
def remove_silence(
    input_path: str,
    min_silence_len: int,
    silence_thresh: float,
    padding: int,
    output: str | None,
) -> None:
    """Strip silent sections from an audio file.

    \b
    Examples:
        musicprod remove-silence recording.wav
        musicprod remove-silence recording.wav --silence-thresh -35 --min-silence-len 300
    """
    from musicprod.tools.silence_remover import remove_silence as _remove

    try:
        click.echo(f"Removing silence from {input_path!r} …")
        result = _remove(
            input_path,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
            padding=padding,
            output_path=output,
        )
        click.secho(f"Saved: {result}", fg="green")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 14 — Channel Converter
# ---------------------------------------------------------------------------

@cli.command("convert-channels")
@click.argument("input_path", metavar="FILE")
@click.option("--channels", default="1", show_default=True, type=click.Choice(["1", "2"]),
              metavar="N", help="Target channel count: 1 (mono) or 2 (stereo).")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Destination file path (default: <stem>_mono/stereo.<ext>).")
def convert_channels(input_path: str, channels: str, output: str | None) -> None:
    """Convert audio between stereo and mono.

    \b
    Examples:
        musicprod convert-channels stereo.mp3 --channels 1
        musicprod convert-channels mono.mp3 --channels 2
    """
    from musicprod.tools.channel_converter import convert_channels as _convert

    try:
        ch = int(channels)
        click.echo(f"Converting {input_path!r} to {'mono' if ch == 1 else 'stereo'} …")
        result = _convert(input_path, channels=ch, output_path=output)
        click.secho(f"Saved: {result}", fg="green")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 15 — Tempo Changer
# ---------------------------------------------------------------------------

@cli.command("change-tempo")
@click.argument("input_path", metavar="FILE")
@click.option("--rate", required=True, type=float, metavar="RATE",
              help="Speed multiplier (e.g. 1.5 = 50%% faster, 0.75 = 25%% slower).")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Destination file path (default: <stem>_tempo.<ext>).")
def change_tempo(input_path: str, rate: float, output: str | None) -> None:
    """Change the playback speed of an audio file without altering its pitch.

    \b
    Examples:
        musicprod change-tempo track.mp3 --rate 1.25
        musicprod change-tempo track.mp3 --rate 0.8 --output slower.mp3
    """
    from musicprod.tools.tempo_changer import change_tempo as _change

    try:
        click.echo(f"Changing tempo of {input_path!r} by {rate}× …")
        result = _change(input_path, rate=rate, output_path=output)
        click.secho(f"Saved: {result}", fg="green")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 16 — Reverb Effect
# ---------------------------------------------------------------------------

@cli.command("add-reverb")
@click.argument("input_path", metavar="FILE")
@click.option("--delay-ms", default=80, show_default=True, type=int, metavar="MS",
              help="Delay between reflections in milliseconds.")
@click.option("--decay", default=0.4, show_default=True, type=float, metavar="FACTOR",
              help="Volume reduction per reflection (0–1).")
@click.option("--reflections", default=5, show_default=True, type=int, metavar="N",
              help="Number of reflected copies (1–20).")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Destination file path (default: <stem>_reverb.<ext>).")
def add_reverb(
    input_path: str,
    delay_ms: int,
    decay: float,
    reflections: int,
    output: str | None,
) -> None:
    """Add a reverb/room effect to an audio file.

    \b
    Examples:
        musicprod add-reverb dry.wav
        musicprod add-reverb dry.wav --delay-ms 120 --decay 0.3 --reflections 8
    """
    from musicprod.tools.reverb_effect import add_reverb as _reverb

    try:
        click.echo(f"Adding reverb to {input_path!r} …")
        result = _reverb(input_path, delay_ms=delay_ms, decay=decay,
                         reflections=reflections, output_path=output)
        click.secho(f"Saved: {result}", fg="green")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 17 — Key Detector
# ---------------------------------------------------------------------------

@cli.command("detect-key")
@click.argument("input_path", metavar="FILE")
def detect_key(input_path: str) -> None:
    """Detect the musical key of an audio file.

    \b
    Example:
        musicprod detect-key track.mp3
    """
    from musicprod.tools.key_detector import detect_key as _detect

    try:
        click.echo(f"Analysing: {input_path}")
        key = _detect(input_path)
        click.secho(f"Detected key: {key}", fg="green")
    except (FileNotFoundError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 18 — Volume Adjuster
# ---------------------------------------------------------------------------

@cli.command("adjust-volume")
@click.argument("input_path", metavar="FILE")
@click.option("--db", required=True, type=float, metavar="DB",
              help="Volume change in dB (positive = louder, negative = quieter).")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Destination file path (default: <stem>_volume.<ext>).")
def adjust_volume(input_path: str, db: float, output: str | None) -> None:
    """Increase or decrease the volume of an audio file.

    \b
    Examples:
        musicprod adjust-volume track.mp3 --db 6
        musicprod adjust-volume track.mp3 --db -3 --output quieter.mp3
    """
    from musicprod.tools.volume_adjuster import adjust_volume as _adjust

    try:
        click.echo(f"Adjusting volume of {input_path!r} by {db:+.1f} dB …")
        result = _adjust(input_path, db=db, output_path=output)
        click.secho(f"Saved: {result}", fg="green")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 19 — Audio Compressor
# ---------------------------------------------------------------------------

@cli.command("compress-audio")
@click.argument("input_path", metavar="FILE")
@click.option("--threshold", default=-20.0, show_default=True, type=float, metavar="DBFS",
              help="Threshold in dBFS above which compression is applied.")
@click.option("--ratio", default=4.0, show_default=True, type=float, metavar="RATIO",
              help="Compression ratio (e.g. 4.0 for 4:1).")
@click.option("--attack", default=5.0, show_default=True, type=float, metavar="MS",
              help="Attack time in milliseconds.")
@click.option("--release", default=50.0, show_default=True, type=float, metavar="MS",
              help="Release time in milliseconds.")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Destination file path (default: <stem>_compressed.<ext>).")
def compress_audio(
    input_path: str,
    threshold: float,
    ratio: float,
    attack: float,
    release: float,
    output: str | None,
) -> None:
    """Apply dynamic range compression to an audio file.

    \b
    Examples:
        musicprod compress-audio track.mp3
        musicprod compress-audio track.mp3 --threshold -15 --ratio 6
    """
    from musicprod.tools.audio_compressor import compress_audio as _compress

    try:
        click.echo(f"Compressing {input_path!r} (threshold={threshold} dBFS, ratio={ratio}:1) …")
        result = _compress(
            input_path,
            threshold=threshold,
            ratio=ratio,
            attack=attack,
            release=release,
            output_path=output,
        )
        click.secho(f"Saved: {result}", fg="green")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 20 — Loop Creator
# ---------------------------------------------------------------------------

@cli.command("create-loop")
@click.argument("input_path", metavar="FILE")
@click.option("--count", default=4, show_default=True, type=int, metavar="N",
              help="Number of times to repeat the audio (>= 2).")
@click.option("--crossfade", default=0, show_default=True, type=int, metavar="MS",
              help="Crossfade duration between repetitions in milliseconds.")
@click.option("--output", "-o", default=None, metavar="FILE",
              help="Destination file path (default: <stem>_loop.<ext>).")
def create_loop(input_path: str, count: int, crossfade: int, output: str | None) -> None:
    """Repeat an audio file N times to create a loop.

    \b
    Examples:
        musicprod create-loop beat.wav --count 8
        musicprod create-loop beat.wav --count 4 --crossfade 50
    """
    from musicprod.tools.loop_creator import create_loop as _loop

    try:
        click.echo(f"Creating {count}× loop of {input_path!r} …")
        result = _loop(input_path, count=count, crossfade=crossfade, output_path=output)
        click.secho(f"Saved: {result}", fg="green")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Tool 21 — Chord Detector
# ---------------------------------------------------------------------------

@cli.command("detect-chords")
@click.argument("input_path", metavar="FILE")
@click.option(
    "--hop-length",
    default=4096,
    show_default=True,
    type=int,
    metavar="SAMPLES",
    help="Chromagram frame size in samples. Larger = smoother boundaries.",
)
@click.option(
    "--min-duration",
    default=0.5,
    show_default=True,
    type=float,
    metavar="SECS",
    help="Merge chord segments shorter than this duration (seconds).",
)
@click.option(
    "--output",
    "-o",
    default=None,
    metavar="FILE",
    help="Optional text file to save the chord list to.",
)
def detect_chords(
    input_path: str,
    hop_length: int,
    min_duration: float,
    output: str | None,
) -> None:
    """Detect the chord progression of an audio file.

    \b
    Examples:
        musicprod detect-chords song.mp3
        musicprod detect-chords song.wav --min-duration 1.0 --output chords.txt
    """
    from musicprod.tools.chord_detector import detect_chords as _detect, format_chords

    try:
        click.echo(f"Analysing chords in {input_path!r} …")
        segments = _detect(input_path, hop_length=hop_length,
                           min_duration=min_duration, output_path=output)
        if not segments:
            click.secho("No chords detected.", fg="yellow")
            return
        click.secho(f"Detected {len(segments)} chord segment(s):", fg="green")
        click.echo(format_chords(segments))
        if output:
            click.secho(f"Saved: {output}", fg="green")
    except (FileNotFoundError, RuntimeError) as exc:
        click.secho(f"Error: {exc}", fg="red", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Update — pull the latest changes from main
# ---------------------------------------------------------------------------

@cli.command("update")
def update() -> None:
    """Update MusicProd to the latest version from the main branch.

    For development (git-clone) installs the command runs ``git pull``
    inside the repository directory.  For regular pip installs it
    upgrades the package via ``pip install --upgrade git+<repo>``.

    \b
    Example:
        musicprod update
    """
    from musicprod.tools.updater import self_update

    click.echo("Checking for updates…")
    try:
        method, message = self_update()
        label = "git pull" if method == "git" else "pip upgrade"
        click.secho(f"[{label}] {message}", fg="green")
    except RuntimeError as exc:
        click.secho(f"Update failed: {exc}", fg="red", err=True)
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
