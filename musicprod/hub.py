"""MusicProd Hub — Tkinter GUI giving access to all 20 music production tools."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, scrolledtext, ttk
from typing import Callable

# ---------------------------------------------------------------------------
# Colour palette (kawaii pink 🌸)
# ---------------------------------------------------------------------------
DARK_BG = "#fff0f6"       # soft blush background
CARD_BG = "#ffe4f0"       # light rose card
SIDEBAR_BG = "#ffd6e8"    # pastel pink sidebar
ACCENT = "#ff69b4"        # hot pink buttons
ACCENT_HOVER = "#ff1493"  # deep pink on hover
TEXT = "#5c1a3a"          # dark berry text
MUTED = "#c0607a"         # muted rose
ERROR_COLOR = "#e8004d"   # vivid red-pink
SUCCESS_COLOR = "#c2185b" # deep pink success
ENTRY_BG = "#ffcce4"      # pale pink inputs


# ---------------------------------------------------------------------------
# Helper widgets
# ---------------------------------------------------------------------------

class _FileEntry(ttk.Frame):
    """A labelled row with a path entry and a Browse button."""

    def __init__(
        self,
        master: tk.Widget,
        label: str,
        mode: str = "open",   # "open" | "save" | "dir"
        filetypes: list[tuple[str, str]] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(master, style="Card.TFrame", **kwargs)
        self._mode = mode
        self._filetypes = filetypes or [("Audio files", "*.mp3 *.wav *.flac *.ogg *.aac *.m4a *.opus"), ("All files", "*.*")]

        ttk.Label(self, text=label, style="Muted.TLabel", width=18, anchor="w").pack(side="left")
        self._var = tk.StringVar()
        self._entry = ttk.Entry(self, textvariable=self._var, style="Dark.TEntry")
        self._entry.pack(side="left", fill="x", expand=True, padx=(4, 4))
        ttk.Button(self, text="Browse…", command=self._browse, style="Small.TButton").pack(side="left")

    def _browse(self) -> None:
        if self._mode == "open":
            path = filedialog.askopenfilename(filetypes=self._filetypes)
        elif self._mode == "save":
            path = filedialog.asksaveasfilename(filetypes=self._filetypes)
        else:
            path = filedialog.askdirectory()
        if path:
            self._var.set(path)

    @property
    def value(self) -> str:
        return self._var.get().strip()

    @value.setter
    def value(self, v: str) -> None:
        self._var.set(v)


class _LabeledEntry(ttk.Frame):
    """A labelled text entry row."""

    def __init__(self, master: tk.Widget, label: str, default: str = "", **kwargs: object) -> None:
        super().__init__(master, style="Card.TFrame", **kwargs)
        ttk.Label(self, text=label, style="Muted.TLabel", width=18, anchor="w").pack(side="left")
        self._var = tk.StringVar(value=default)
        ttk.Entry(self, textvariable=self._var, style="Dark.TEntry").pack(side="left", fill="x", expand=True)

    @property
    def value(self) -> str:
        return self._var.get().strip()


# ---------------------------------------------------------------------------
# Individual tool panels
# ---------------------------------------------------------------------------

class _ToolPanel(ttk.Frame):
    """Base class for a tool panel."""

    title: str = ""
    icon: str = ""
    help_text: str = ""

    def __init__(self, master: tk.Widget, log: Callable[[str, str], None]) -> None:
        super().__init__(master, style="Card.TFrame")
        self._log = log
        self._build()
        if self.help_text:
            btn = ttk.Button(self, text="❓  Help", command=self._show_help, style="Small.TButton")
            btn.place(relx=1.0, y=8, anchor="ne", x=-8)

    def _show_help(self) -> None:
        """Open a help window for this tool."""
        win = tk.Toplevel(self)
        win.title(f"Help — {self.title}")
        win.geometry("540x460")
        win.configure(bg=DARK_BG)
        win.resizable(True, True)
        win.grab_set()

        ttk.Label(
            win,
            text=f"{self.icon}  {self.title}",
            style="Title.TLabel",
            padding=(16, 12, 0, 4),
        ).pack(anchor="w")
        ttk.Separator(win, orient="horizontal").pack(fill="x", pady=(0, 8))

        txt = scrolledtext.ScrolledText(
            win,
            wrap="word",
            bg=CARD_BG,
            fg=TEXT,
            font=("Segoe UI", 10),
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
        )
        txt.pack(fill="both", expand=True, padx=12, pady=(0, 4))
        txt.tag_configure("heading", foreground=ACCENT, font=("Segoe UI", 10, "bold"))
        txt.tag_configure("bullet", lmargin1=8, lmargin2=20)
        for line in self.help_text.splitlines(keepends=True):
            stripped = line.rstrip()
            is_heading = (
                stripped
                and any(c.isalpha() for c in stripped)
                and (stripped == stripped.upper() or stripped.startswith("─"))
            )
            if is_heading:
                txt.insert("end", line, "heading")
            elif stripped.startswith("•"):
                txt.insert("end", line, "bullet")
            else:
                txt.insert("end", line)
        txt.configure(state="disabled")

        ttk.Button(win, text="Close", command=win.destroy, style="Small.TButton").pack(pady=(0, 12))

    def _build(self) -> None:
        raise NotImplementedError

    def _run_in_thread(self, fn: Callable[[], None]) -> None:
        threading.Thread(target=fn, daemon=True).start()

    def _row(self) -> ttk.Frame:
        f = ttk.Frame(self, style="Card.TFrame")
        f.pack(fill="x", padx=16, pady=4)
        return f


class _YouTubePanel(_ToolPanel):
    title = "YouTube → MP3"
    icon = "🎵"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Downloads audio from a YouTube video and saves it as an MP3 file.
Requires an active internet connection and yt-dlp.

PARAMETERS
─────────────────────────────────────────────────────
• YouTube URL — The full URL of the YouTube video
  (e.g. https://www.youtube.com/watch?v=dQw4w9WgXcQ).
• Output file (.mp3) — Where to save the resulting MP3. Leave blank
  to save in the current working directory using the video title.

TIPS & TRICKS
─────────────────────────────────────────────────────
• Paste the URL directly from your browser's address bar.
• Age-restricted or private videos cannot be downloaded.
• Leaving the output path blank lets yt-dlp derive a clean filename
  from the video title automatically.
• Downloaded audio is encoded at 192 kbps by default.
• Works with YouTube Shorts URLs as well as standard watch URLs.
"""

    def _build(self) -> None:
        ttk.Label(self, text="Download audio from YouTube as MP3 ♪", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        ttk.Label(r1, text="YouTube URL", style="Muted.TLabel", width=18, anchor="w").pack(side="left")
        self._url = tk.StringVar()
        ttk.Entry(r1, textvariable=self._url, style="Dark.TEntry").pack(side="left", fill="x", expand=True)

        r2 = self._row()
        self._out = _FileEntry(r2, "Output file (.mp3)", mode="save", filetypes=[("MP3", "*.mp3"), ("All files", "*.*")])
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="🎵  Download", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        url = self._url.get().strip()
        if not url:
            self._log("Please enter a YouTube URL.", "error")
            return
        out = self._out.value or None
        self._log(f"Downloading: {url}", "info")
        def task() -> None:
            try:
                from musicprod.tools.youtube_to_mp3 import download_youtube_to_mp3
                result = download_youtube_to_mp3(url, output_path=out)
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _BPMPanel(_ToolPanel):
    title = "BPM Detector"
    icon = "🥁"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Analyses an audio file and estimates its Beats Per Minute (BPM) —
the tempo or speed of the music.

PARAMETERS
─────────────────────────────────────────────────────
• Audio file — Any common audio format (MP3, WAV, FLAC, OGG …).

TIPS & TRICKS
─────────────────────────────────────────────────────
• BPM detection works best on rhythmically clear material (drums,
  percussion, electronic music). Results may be less accurate for
  ambient, classical, or rubato recordings.
• Common BPM ranges by genre:
    60–80    Ballad / Slow
    80–110   Pop / R&B
   110–130   House / Hip-Hop
   128–145   EDM / Techno
   160–180   Drum & Bass / Hardcore
• If the result seems halved or doubled, try multiplying or dividing
  by 2 — tempo ambiguity is common in automated detection.
• For best accuracy, use a lossless format (WAV or FLAC).
"""

    def _build(self) -> None:
        ttk.Label(self, text="Detect the tempo (BPM) of an audio file 🎶", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Audio file")
        self._file.pack(fill="x", expand=True)
        ttk.Button(self, text="🥁  Detect BPM", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an audio file.", "error")
            return
        self._log(f"Analysing: {path}", "info")
        def task() -> None:
            try:
                from musicprod.tools.bpm_detector import detect_bpm
                bpm = detect_bpm(path)
                self._log(f"Detected BPM: {bpm}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _FormatPanel(_ToolPanel):
    title = "Format Converter"
    icon = "🔄"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Converts an audio file from one format to another.
Supported formats: MP3, WAV, FLAC, OGG, AAC, M4A, OPUS.
Requires FFmpeg to be installed on your system.

PARAMETERS
─────────────────────────────────────────────────────
• Input file — The source audio file to convert.
• Target format — The output format to convert to.
• Output file (opt.) — Where to save the converted file. Leave blank
  to save next to the input file with the new extension.

TIPS & TRICKS
─────────────────────────────────────────────────────
• WAV and FLAC are lossless (no quality loss, larger file size).
  Use these for mastering, editing, or archiving.
• MP3 and OGG are lossy (smaller file size, slight quality loss).
  Use these for streaming and general playback.
• OPUS offers excellent quality at very low bitrates — great for
  podcasts and voice recordings.
• AAC / M4A is the standard format for Apple devices and iTunes.
• Converting between two lossy formats (e.g. MP3 → OGG) introduces
  generation loss — convert from a lossless source whenever possible.
"""

    def _build(self) -> None:
        ttk.Label(self, text="Convert audio between formats (MP3, WAV, FLAC, OGG …) ✨", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        ttk.Label(r2, text="Target format", style="Muted.TLabel", width=18, anchor="w").pack(side="left")
        self._fmt = ttk.Combobox(r2, values=["mp3", "wav", "flac", "ogg", "aac", "m4a", "opus"], state="readonly", width=10)
        self._fmt.set("mp3")
        self._fmt.pack(side="left")

        r3 = self._row()
        self._out = _FileEntry(r3, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="🔄  Convert", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an input file.", "error")
            return
        fmt = self._fmt.get()
        out = self._out.value or None
        self._log(f"Converting {path!r} → {fmt.upper()} …", "info")
        def task() -> None:
            try:
                from musicprod.tools.format_converter import convert_format
                result = convert_format(path, fmt, output_path=out)
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _TrimPanel(_ToolPanel):
    title = "Audio Trimmer"
    icon = "✂️"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Trims an audio file to the specified start and end timestamps, keeping
only the audio between those two points.
Requires FFmpeg to be installed on your system.

PARAMETERS
─────────────────────────────────────────────────────
• Input file — The source audio file to trim.
• Start time — The point in the audio to start keeping.
  Accepted formats: M:SS, MM:SS, H:MM:SS, or plain seconds (e.g. 90).
• End time — The point at which to stop (exclusive).
  Same format as Start time.
• Output file (opt.) — Where to save the trimmed file. Leave blank to
  auto-generate a name next to the input file.

TIPS & TRICKS
─────────────────────────────────────────────────────
• To trim from the beginning: set Start time to 0:00.
• To trim to a specific duration rather than an end point, calculate
  end = start + desired_duration in seconds.
• Trimming a lossless format (WAV, FLAC) preserves full quality.
• To make multiple clips from one file, use the Audio Splitter tool.
• Use the Waveform Plotter first to visually identify exact timestamps.
"""

    def _build(self) -> None:
        ttk.Label(self, text="Trim an audio file to a start/end timestamp 🎀", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._start = _LabeledEntry(r2, "Start time (MM:SS)", "0:00")
        self._start.pack(fill="x", expand=True)

        r3 = self._row()
        self._end = _LabeledEntry(r3, "End time (MM:SS)", "0:30")
        self._end.pack(fill="x", expand=True)

        r4 = self._row()
        self._out = _FileEntry(r4, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="✂️  Trim", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an input file.", "error")
            return
        start = self._start.value
        end = self._end.value
        out = self._out.value or None
        self._log(f"Trimming {path!r} from {start} to {end} …", "info")
        def task() -> None:
            try:
                from musicprod.tools.audio_trimmer import trim_audio
                result = trim_audio(path, start, end, output_path=out)
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _MetadataPanel(_ToolPanel):
    title = "Metadata Editor"
    icon = "🏷️"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Reads and writes ID3 / Vorbis Comment metadata tags embedded in an
audio file (title, artist, album, genre, and more).

PARAMETERS
─────────────────────────────────────────────────────
• Audio file — The file whose tags you want to read or edit.
• Title — The name of the track.
• Artist — The performing artist or band.
• Album — The album the track belongs to.
• Albumartist — The main artist for the entire album (useful when
  compilations have per-track artists).
• Genre — Musical genre (e.g. Pop, Rock, Electronic).
• Date — Release year or full date (e.g. 2024 or 2024-06-15).
• Tracknumber — Position in the album (e.g. 1 or 1/12).
• Comment — Free-form notes or additional information.

TIPS & TRICKS
─────────────────────────────────────────────────────
• Click "Read Tags" first to load any existing metadata into the
  fields before editing, to avoid overwriting information.
• Leave a field blank to clear that tag when saving.
• ID3 tags are supported in MP3; Vorbis Comments in FLAC/OGG.
• Proper metadata helps music players, DJ software, and streaming
  platforms display and organise your tracks correctly.
• For compilations set Albumartist to "Various Artists" so the
  whole album groups together in most music libraries.
"""

    def _build(self) -> None:
        ttk.Label(self, text="View or edit audio file metadata tags 🌸", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Audio file")
        self._file.pack(fill="x", expand=True)

        btn_row = ttk.Frame(self, style="Card.TFrame")
        btn_row.pack(padx=16, pady=(0, 8))
        ttk.Button(btn_row, text="🔍  Read Tags", command=self._read, style="Accent.TButton").pack(side="left", padx=(0, 8))
        tags = ["title", "artist", "album", "albumartist", "genre", "date", "tracknumber", "comment"]
        self._tag_vars: dict[str, _LabeledEntry] = {}
        for tag in tags:
            r = self._row()
            entry = _LabeledEntry(r, tag.capitalize())
            entry.pack(fill="x", expand=True)
            self._tag_vars[tag] = entry

        ttk.Button(self, text="💾  Save Tags", command=self._write, style="Accent.TButton").pack(pady=(0, 12))

    def _read(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an audio file.", "error")
            return
        def task() -> None:
            try:
                from musicprod.tools.metadata_editor import read_metadata
                tags = read_metadata(path)
                for key, entry in self._tag_vars.items():
                    entry.value = str(tags.get(key, ""))
                self._log("Metadata loaded.", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)

    def _write(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an audio file.", "error")
            return
        kwargs = {k: v.value or None for k, v in self._tag_vars.items()}
        def task() -> None:
            try:
                from musicprod.tools.metadata_editor import write_metadata
                write_metadata(path, **kwargs)
                self._log("Metadata saved successfully.", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _NormalizePanel(_ToolPanel):
    title = "Audio Normalizer"
    icon = "🌈"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Adjusts the overall volume of an audio file so its peak loudness
reaches the specified dBFS (decibels relative to Full Scale) level.

PARAMETERS
─────────────────────────────────────────────────────
• Input file — The audio file to normalize.
• Target dBFS — The desired peak level. Must be a negative number or
  zero (0.0 = maximum possible without clipping).
• Output file (opt.) — Where to save the normalized file.

TIPS & TRICKS
─────────────────────────────────────────────────────
• dBFS is always ≤ 0. A value of 0.0 is the absolute loudest a
  digital signal can go without clipping.
• Recommended target levels:
    -14.0  Streaming platforms (Spotify, YouTube Music)
     -9.0  Broadcast / TV
     -6.0  Headroom for further mixing / mastering
     -1.0  Final master just before distribution
• Normalization raises or lowers the entire file uniformly — it does
  not compress dynamic range. For dynamic control use the
  Audio Compressor tool.
• Normalize to -14.0 dBFS before uploading to Spotify or Apple Music
  to match their loudness targets (they will turn down louder tracks).
"""

    def _build(self) -> None:
        ttk.Label(self, text="Normalize audio loudness to a target dBFS level ✨", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._dbfs = _LabeledEntry(r2, "Target dBFS", "-14.0")
        self._dbfs.pack(fill="x", expand=True)

        r3 = self._row()
        self._out = _FileEntry(r3, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="🌈  Normalize", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an input file.", "error")
            return
        try:
            dbfs = float(self._dbfs.value)
        except ValueError:
            self._log("Target dBFS must be a number.", "error")
            return
        out = self._out.value or None
        self._log(f"Normalizing {path!r} to {dbfs} dBFS …", "info")
        def task() -> None:
            try:
                from musicprod.tools.audio_normalizer import normalize_audio
                result = normalize_audio(path, target_dbfs=dbfs, output_path=out)
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _PitchPanel(_ToolPanel):
    title = "Pitch Shifter"
    icon = "🎹"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Shifts the pitch of an audio file up or down by a given number of
semitones without changing its playback speed.

PARAMETERS
─────────────────────────────────────────────────────
• Input file — The audio file to pitch-shift.
• Semitones — How many semitones to shift.
  Positive values = pitch up (higher).
  Negative values = pitch down (lower).
• Output file (opt.) — Where to save the result.

TIPS & TRICKS
─────────────────────────────────────────────────────
• 1 semitone = one piano key. 12 semitones = one full octave.
• Common creative uses:
    +2  Slightly brighter, more energetic feel
    -2  Darker, more mellow feel
   +12  One octave up (e.g. turn bass into mid-range)
   -12  One octave down
• Fractional semitones are supported (e.g. 0.5 for fine-tuning).
• Large shifts (> ±6 semitones) may introduce audible artefacts.
• To change speed without changing pitch, use the Tempo Changer tool.
• To detect what key the audio is already in, use the Key Detector.
"""

    def _build(self) -> None:
        ttk.Label(self, text="Shift the pitch of an audio file by semitones 🎶", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._semi = _LabeledEntry(r2, "Semitones", "2")
        self._semi.pack(fill="x", expand=True)

        r3 = self._row()
        self._out = _FileEntry(r3, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="🎹  Shift Pitch", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an input file.", "error")
            return
        try:
            semitones = float(self._semi.value)
        except ValueError:
            self._log("Semitones must be a number.", "error")
            return
        out = self._out.value or None
        self._log(f"Shifting pitch of {path!r} by {semitones:+.1f} semitones …", "info")
        def task() -> None:
            try:
                from musicprod.tools.pitch_shifter import shift_pitch
                result = shift_pitch(path, semitones=semitones, output_path=out)
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _SplitPanel(_ToolPanel):
    title = "Audio Splitter"
    icon = "🍰"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Splits an audio file into equal-length chunks of a specified duration.
Useful for dividing long recordings, podcasts, or albums into segments.

PARAMETERS
─────────────────────────────────────────────────────
• Input file — The audio file to split.
• Chunk duration (s) — Length of each chunk in seconds. The last
  chunk will be shorter if the total duration is not evenly divisible.
• Output dir (opt.) — Folder where chunks will be saved. Leave blank
  to save in the same directory as the input file.

TIPS & TRICKS
─────────────────────────────────────────────────────
• Chunks are named automatically: <original_name>_part001.ext,
  <original_name>_part002.ext, and so on.
• For splitting by silence rather than fixed duration, see the
  Silence Remover tool.
• Common chunk durations:
    30 s   Social media clips / sample previews
    60 s   Short podcast segments
   300 s   Podcast chapters (5 min)
  1800 s   Broadcast-safe segments (30 min)
• Splitting does not re-encode the audio — quality is preserved.
"""

    def _build(self) -> None:
        ttk.Label(self, text="Split an audio file into equal-duration chunks 🍰", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._dur = _LabeledEntry(r2, "Chunk duration (s)", "30")
        self._dur.pack(fill="x", expand=True)

        r3 = self._row()
        self._outdir = _FileEntry(r3, "Output dir (opt.)", mode="dir")
        self._outdir.pack(fill="x", expand=True)

        ttk.Button(self, text="🍰  Split", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an input file.", "error")
            return
        try:
            dur = float(self._dur.value)
        except ValueError:
            self._log("Chunk duration must be a number.", "error")
            return
        out_dir = self._outdir.value or None
        self._log(f"Splitting {path!r} into {dur}s chunks …", "info")
        def task() -> None:
            try:
                from musicprod.tools.audio_splitter import split_audio
                chunks = split_audio(path, chunk_duration=dur, output_dir=out_dir)
                self._log(f"Created {len(chunks)} chunk(s):", "success")
                for c in chunks:
                    self._log(f"  {c}", "info")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _MergePanel(_ToolPanel):
    title = "Audio Merger"
    icon = "💞"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Concatenates two or more audio files end-to-end into a single file.
Useful for joining podcast segments, album tracks, or samples.

PARAMETERS
─────────────────────────────────────────────────────
• File 1, File 2, … — The source audio files to join.
  Files are merged in the order they appear. Use "+ Add file" to
  include more than two inputs.
• Output file (opt.) — Where to save the merged file. Leave blank to
  auto-generate a filename next to the first input file.

TIPS & TRICKS
─────────────────────────────────────────────────────
• The order of files matters — they are joined top-to-bottom as
  listed in the UI.
• For the best results all input files should have the same sample
  rate, channel count, and format. Mismatched files will be
  re-encoded to match the first file's properties.
• To add a smooth transition between clips, apply the Fade Effect to
  each segment (fade out the end, fade in the start) before merging.
• Use the Loop Creator tool if you want to repeat a single file
  multiple times instead of merging different files.
"""

    def __init__(self, master: tk.Widget, log: Callable[[str, str], None]) -> None:
        self._file_entries: list[_FileEntry] = []
        super().__init__(master, log)

    def _build(self) -> None:
        ttk.Label(self, text="Merge/concatenate multiple audio files into one 💞", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))

        self._files_frame = ttk.Frame(self, style="Card.TFrame")
        self._files_frame.pack(fill="x", padx=16)

        for _ in range(2):
            self._add_file_row()

        btn_row = ttk.Frame(self, style="Card.TFrame")
        btn_row.pack(padx=16, pady=(4, 8))
        ttk.Button(btn_row, text="+ Add file", command=self._add_file_row, style="Small.TButton").pack(side="left", padx=(0, 8))
        r_out = self._row()
        self._out = _FileEntry(r_out, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="💞  Merge", command=self._run, style="Accent.TButton").pack(pady=12)

    def _add_file_row(self) -> None:
        fe = _FileEntry(self._files_frame, f"File {len(self._file_entries) + 1}")
        fe.pack(fill="x", pady=2)
        self._file_entries.append(fe)

    def _run(self) -> None:
        paths = [fe.value for fe in self._file_entries if fe.value]
        if len(paths) < 2:
            self._log("Please select at least two input files.", "error")
            return
        out = self._out.value or None
        self._log(f"Merging {len(paths)} file(s) …", "info")
        def task() -> None:
            try:
                from musicprod.tools.audio_merger import merge_audio
                result = merge_audio(paths, output_path=out)
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _WaveformPanel(_ToolPanel):
    title = "Waveform Plotter"
    icon = "🌊"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Generates a waveform image (PNG) that visualises the amplitude of an
audio file over time. Useful for reviewing dynamics at a glance.

PARAMETERS
─────────────────────────────────────────────────────
• Input file — The audio file to visualise.
• Output PNG (opt.) — Where to save the image. Leave blank to save
  next to the input file with a .png extension.

TIPS & TRICKS
─────────────────────────────────────────────────────
• The horizontal axis represents time; the vertical axis represents
  amplitude (loudness). Taller peaks = louder moments.
• A flat-topped waveform ("brickwall") indicates heavy limiting or
  clipping — the audio may sound distorted.
• A lot of empty space (very low amplitude) may indicate silence or
  noise that can be removed with the Silence Remover tool.
• Use the waveform image to identify precise trim points before
  using the Audio Trimmer tool.
• The image can be embedded in documentation, podcast show notes, or
  used as album artwork / social media previews.
"""

    def _build(self) -> None:
        ttk.Label(self, text="Generate a waveform PNG image of an audio file 🌊", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._out = _FileEntry(r2, "Output PNG (opt.)", mode="save", filetypes=[("PNG image", "*.png"), ("All files", "*.*")])
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="🌊  Plot Waveform", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an input file.", "error")
            return
        out = self._out.value or None
        self._log(f"Plotting waveform for {path!r} …", "info")
        def task() -> None:
            try:
                from musicprod.tools.waveform_plotter import plot_waveform
                result = plot_waveform(path, output_path=out)
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _NoiseReducerPanel(_ToolPanel):
    title = "Noise Reducer"
    icon = "🔇"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Reduces steady background noise (hiss, hum, room noise, fan noise)
from an audio file using spectral subtraction.

PARAMETERS
─────────────────────────────────────────────────────
• Input file — The audio file to clean up.
• Noise duration (s) — Length (in seconds) of a section at the START
  of the file that contains only background noise (no speech/music).
  This "noise profile" is used to identify what to remove.
• Strength (0–3) — How aggressively to suppress the noise.
  0.0 = no reduction. 1.0 = standard. Higher values remove more noise
  but may introduce "watery" artefacts.
• Output file (opt.) — Where to save the cleaned file.

TIPS & TRICKS
─────────────────────────────────────────────────────
• Record a few seconds of pure room/background noise at the start of
  your recording specifically for use as a noise profile.
• Start with Strength 1.0 and increase only if noise is still audible.
• Strength above 2.0 often causes musical noise ("warbling") —
  use carefully.
• This tool works best on continuous, steady noise (fans, hum).
  It is less effective on intermittent noise (clicks, pops).
• For click/pop removal, consider running the audio through a DAW
  with dedicated click-removal plugins.
"""

    def _build(self) -> None:
        ttk.Label(self, text="Reduce background noise via spectral subtraction 🔇", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._noise_dur = _LabeledEntry(r2, "Noise duration (s)", "0.5")
        self._noise_dur.pack(fill="x", expand=True)

        r3 = self._row()
        self._strength = _LabeledEntry(r3, "Strength (0–3)", "1.0")
        self._strength.pack(fill="x", expand=True)

        r4 = self._row()
        self._out = _FileEntry(r4, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="🔇  Reduce Noise", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an input file.", "error")
            return
        try:
            noise_dur = float(self._noise_dur.value)
            strength = float(self._strength.value)
        except ValueError:
            self._log("Noise duration and strength must be numbers.", "error")
            return
        out = self._out.value or None
        self._log(f"Reducing noise in {path!r} …", "info")
        def task() -> None:
            try:
                from musicprod.tools.noise_reducer import reduce_noise
                result = reduce_noise(path, noise_duration=noise_dur, strength=strength, output_path=out)
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _FadePanel(_ToolPanel):
    title = "Fade Effect"
    icon = "🌅"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Applies a fade-in (gradual volume increase at the start) and/or a
fade-out (gradual volume decrease at the end) to an audio file.

PARAMETERS
─────────────────────────────────────────────────────
• Input file — The audio file to apply fades to.
• Fade-in (s) — Duration of the fade-in in seconds.
  Set to 0.0 to skip the fade-in.
• Fade-out (s) — Duration of the fade-out in seconds.
  Set to 0.0 to skip the fade-out.
• Output file (opt.) — Where to save the result.

TIPS & TRICKS
─────────────────────────────────────────────────────
• A fade-in of 0.5–2 s is natural for most music tracks.
• A fade-out of 3–8 s feels smooth on most tracks.
• Use short fades (0.05–0.2 s) to avoid clicks/pops when joining
  clips in the Audio Merger tool.
• Very long fade-outs (15–30 s) create a cinematic "ambient" ending.
• Apply fade-in to clips that start abruptly to soften the entry.
• Setting both to 0.0 and using this tool simply passes the audio
  through unchanged.
"""

    def _build(self) -> None:
        ttk.Label(self, text="Add fade-in / fade-out to an audio file 🌅", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._fade_in = _LabeledEntry(r2, "Fade-in (s)", "0.0")
        self._fade_in.pack(fill="x", expand=True)

        r3 = self._row()
        self._fade_out = _LabeledEntry(r3, "Fade-out (s)", "2.0")
        self._fade_out.pack(fill="x", expand=True)

        r4 = self._row()
        self._out = _FileEntry(r4, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="🌅  Apply Fade", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an input file.", "error")
            return
        try:
            fade_in = float(self._fade_in.value)
            fade_out = float(self._fade_out.value)
        except ValueError:
            self._log("Fade durations must be numbers.", "error")
            return
        out = self._out.value or None
        self._log(f"Adding fade to {path!r} (in={fade_in}s, out={fade_out}s) …", "info")
        def task() -> None:
            try:
                from musicprod.tools.fade_effect import add_fade
                result = add_fade(path, fade_in=fade_in, fade_out=fade_out, output_path=out)
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _SilenceRemoverPanel(_ToolPanel):
    title = "Silence Remover"
    icon = "🤫"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Detects and removes sections of silence from an audio file, joining
the remaining audio segments together.

PARAMETERS
─────────────────────────────────────────────────────
• Input file — The audio file to process.
• Min silence (ms) — Minimum length of a silent section (in
  milliseconds) to be considered as silence and removed.
  Shorter gaps are kept. Default: 500 ms.
• Threshold (dBFS) — Volume level below which audio is considered
  silent. Default: -40.0 dBFS.
  Lower (more negative) = only very quiet sections are removed.
  Higher (less negative, e.g. -20) = more sections treated as silent.
• Padding (ms) — How many milliseconds to keep at the start and end
  of each audio segment (prevents cutting speech too abruptly).
• Output file (opt.) — Where to save the result.

TIPS & TRICKS
─────────────────────────────────────────────────────
• For podcast/interview editing: Threshold -35, Min silence 300 ms,
  Padding 100 ms gives natural-sounding results.
• For music with natural breathing room, use a longer Min silence
  (1000–2000 ms) so musical pauses are kept.
• Too aggressive a threshold can cut off soft notes or quiet speech.
  Start conservative and adjust step by step.
• Padding prevents the "clipped words" effect where the beginning or
  end of a syllable gets cut off.
"""

    def _build(self) -> None:
        ttk.Label(self, text="Strip silent sections from an audio file 🤫", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._min_sil = _LabeledEntry(r2, "Min silence (ms)", "500")
        self._min_sil.pack(fill="x", expand=True)

        r3 = self._row()
        self._thresh = _LabeledEntry(r3, "Threshold (dBFS)", "-40.0")
        self._thresh.pack(fill="x", expand=True)

        r4 = self._row()
        self._padding = _LabeledEntry(r4, "Padding (ms)", "100")
        self._padding.pack(fill="x", expand=True)

        r5 = self._row()
        self._out = _FileEntry(r5, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="🤫  Remove Silence", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an input file.", "error")
            return
        try:
            min_sil = int(self._min_sil.value)
            thresh = float(self._thresh.value)
            padding = int(self._padding.value)
        except ValueError:
            self._log("Min silence, threshold, and padding must be numbers.", "error")
            return
        out = self._out.value or None
        self._log(f"Removing silence from {path!r} …", "info")
        def task() -> None:
            try:
                from musicprod.tools.silence_remover import remove_silence
                result = remove_silence(path, min_silence_len=min_sil,
                                        silence_thresh=thresh, padding=padding, output_path=out)
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _ChannelPanel(_ToolPanel):
    title = "Channel Converter"
    icon = "🎧"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Converts an audio file between stereo (2-channel) and mono (1-channel).

PARAMETERS
─────────────────────────────────────────────────────
• Input file — The audio file to convert.
• Target channels:
    1 (mono)   — Mixes the left and right channels into one channel.
    2 (stereo) — Duplicates the mono channel to both L and R channels.
• Output file (opt.) — Where to save the result.

TIPS & TRICKS
─────────────────────────────────────────────────────
• Mono is ideal for:
    - Podcasts and voice recordings (smaller file, mono playback)
    - DJ monitoring (check for phase issues)
    - Ringtones and alert sounds
• Stereo is ideal for:
    - Music with spatial width (panning, stereo effects)
    - Film/video audio
• Converting stereo → mono checks for phase cancellation: if the left
  and right channels are out of phase, mixing them will cause certain
  frequencies to cancel out, resulting in a thin or hollow sound.
• Use the Waveform Plotter on both L and R channels to spot obvious
  stereo imbalances before converting.
"""

    def _build(self) -> None:
        ttk.Label(self, text="Convert audio between stereo and mono 🎧", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        ttk.Label(r2, text="Target channels", style="Muted.TLabel", width=18, anchor="w").pack(side="left")
        self._channels = ttk.Combobox(r2, values=["1 (mono)", "2 (stereo)"], state="readonly", width=14)
        self._channels.set("1 (mono)")
        self._channels.pack(side="left")

        r3 = self._row()
        self._out = _FileEntry(r3, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="🎧  Convert", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an input file.", "error")
            return
        ch = 1 if self._channels.get().startswith("1") else 2
        out = self._out.value or None
        label = "mono" if ch == 1 else "stereo"
        self._log(f"Converting {path!r} to {label} …", "info")
        def task() -> None:
            try:
                from musicprod.tools.channel_converter import convert_channels
                result = convert_channels(path, channels=ch, output_path=out)
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _TempoPanel(_ToolPanel):
    title = "Tempo Changer"
    icon = "⏩"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Changes the playback speed of an audio file without altering its pitch
(time-stretching).

PARAMETERS
─────────────────────────────────────────────────────
• Input file — The audio file to time-stretch.
• Speed rate — The playback speed multiplier.
  1.0 = original speed.
  Values > 1.0 = faster (e.g. 1.5 = 50% faster).
  Values < 1.0 = slower (e.g. 0.75 = 25% slower).
• Output file (opt.) — Where to save the result.

TIPS & TRICKS
─────────────────────────────────────────────────────
• Practical rates for common use cases:
    0.75  Slow down for practice / transcription
    0.90  Slightly slower for accessibility
    1.10  Subtly faster, saves a little time
    1.25  Speed-listening (podcasts, lectures)
    1.50  Fast review
    2.00  Double speed
• Extreme stretching (< 0.5 or > 2.0) may produce audible artefacts.
• This tool preserves pitch. If you want to change pitch instead,
  use the Pitch Shifter tool.
• Combining tempo change + pitch shift lets you emulate a vinyl
  speed change effect (try rate 1.05 and semitones +0.8).
"""

    def _build(self) -> None:
        ttk.Label(self, text="Change playback speed without altering pitch ⏩", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._rate = _LabeledEntry(r2, "Speed rate", "1.25")
        self._rate.pack(fill="x", expand=True)

        r3 = self._row()
        self._out = _FileEntry(r3, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="⏩  Change Tempo", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an input file.", "error")
            return
        try:
            rate = float(self._rate.value)
        except ValueError:
            self._log("Rate must be a number.", "error")
            return
        out = self._out.value or None
        self._log(f"Changing tempo of {path!r} by {rate}× …", "info")
        def task() -> None:
            try:
                from musicprod.tools.tempo_changer import change_tempo
                result = change_tempo(path, rate=rate, output_path=out)
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _ReverbPanel(_ToolPanel):
    title = "Reverb Effect"
    icon = "🏛️"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Adds a reverb (room ambience / echo) effect to an audio file by
mixing in multiple delayed and decayed copies of the signal.

PARAMETERS
─────────────────────────────────────────────────────
• Input file — The audio file to add reverb to.
• Delay (ms) — Time between each reflection in milliseconds.
  Higher = larger apparent room size.
  Typical range: 20–200 ms.
• Decay (0–1) — How quickly the reflections fade out.
  0.0 = instant silence (no reverb tail).
  1.0 = reflections never fade (infinite reverb — use carefully!).
  Typical range: 0.2–0.7.
• Reflections — Number of echo copies to add.
  More = longer, denser reverb tail.
  Typical range: 3–15.
• Output file (opt.) — Where to save the result.

TIPS & TRICKS
─────────────────────────────────────────────────────
• Preset ideas:
    Small room:  delay=30  decay=0.2 reflections=4
    Studio:      delay=60  decay=0.35 reflections=6
    Hall:        delay=100 decay=0.5  reflections=10
    Cathedral:   delay=180 decay=0.7  reflections=15
• Too much reverb can make vocals sound distant or muddy.
  Use sparingly on speech and podcast content.
• For music production, apply reverb to individual tracks in a DAW
  for more control than whole-file processing.
"""

    def _build(self) -> None:
        ttk.Label(self, text="Add a reverb/room effect to an audio file 🏛️", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._delay = _LabeledEntry(r2, "Delay (ms)", "80")
        self._delay.pack(fill="x", expand=True)

        r3 = self._row()
        self._decay = _LabeledEntry(r3, "Decay (0–1)", "0.4")
        self._decay.pack(fill="x", expand=True)

        r4 = self._row()
        self._reflections = _LabeledEntry(r4, "Reflections", "5")
        self._reflections.pack(fill="x", expand=True)

        r5 = self._row()
        self._out = _FileEntry(r5, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="🏛️  Add Reverb", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an input file.", "error")
            return
        try:
            delay = int(self._delay.value)
            decay = float(self._decay.value)
            reflections = int(self._reflections.value)
        except ValueError:
            self._log("Delay, decay, and reflections must be numbers.", "error")
            return
        out = self._out.value or None
        self._log(f"Adding reverb to {path!r} …", "info")
        def task() -> None:
            try:
                from musicprod.tools.reverb_effect import add_reverb
                result = add_reverb(path, delay_ms=delay, decay=decay,
                                    reflections=reflections, output_path=out)
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _KeyDetectorPanel(_ToolPanel):
    title = "Key Detector"
    icon = "🗝️"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Analyses the harmonic content of an audio file and estimates the
musical key (e.g. C major, A minor) using the Krumhansl–Kessler
key-finding algorithm.

PARAMETERS
─────────────────────────────────────────────────────
• Audio file — Any common audio format (MP3, WAV, FLAC, OGG …).

TIPS & TRICKS
─────────────────────────────────────────────────────
• Key detection is an estimate. Songs with complex modulations,
  mixed tonalities, or strong dissonance may give ambiguous results.
• Use the result to find harmonically compatible tracks for:
    - DJ mixing (compatible keys won't clash)
    - Mashup creation
    - Sampling (matching a sample to your track's key)
• The Camelot Wheel is a popular DJ reference for compatible keys:
    Matching key numbers (same or ±1) on the wheel mix smoothly.
    Relative major/minor pairs (e.g. C major / A minor) also mix well.
• For best accuracy use a high-quality, lossless source (WAV or FLAC).
• A full-length track gives more accurate results than a short clip.
• If the detected key seems wrong, try shifting pitch by ±1–2 semitones
  and re-detecting to identify possible enharmonic equivalents.
"""

    def _build(self) -> None:
        ttk.Label(self, text="Detect the musical key of an audio file 🗝️", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Audio file")
        self._file.pack(fill="x", expand=True)
        ttk.Button(self, text="🗝️  Detect Key", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an audio file.", "error")
            return
        self._log(f"Analysing: {path}", "info")
        def task() -> None:
            try:
                from musicprod.tools.key_detector import detect_key
                key = detect_key(path)
                self._log(f"Detected key: {key}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _VolumePanel(_ToolPanel):
    title = "Volume Adjuster"
    icon = "🔊"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Increases or decreases the overall volume of an audio file by a
specified number of decibels (dB).

PARAMETERS
─────────────────────────────────────────────────────
• Input file — The audio file to adjust.
• Volume (dB) — Number of decibels to add to the volume.
  Positive values make the audio louder (e.g. +6.0 = twice as loud).
  Negative values make it quieter (e.g. -6.0 = half as loud).
• Output file (opt.) — Where to save the result.

TIPS & TRICKS
─────────────────────────────────────────────────────
• The decibel (dB) scale is logarithmic:
    +6 dB  ≈ double the perceived loudness
    -6 dB  ≈ half the perceived loudness
    +3 dB  ≈ noticeably louder
    -3 dB  ≈ noticeably quieter
• Be careful with large positive values — they can cause clipping
  (distortion) if the waveform hits 0 dBFS.
• To raise volume without risk of clipping, use the Audio Normalizer
  tool instead (it automatically finds a safe target level).
• Lowering volume is safe in any amount; there is no lower limit.
• Use the Waveform Plotter before and after to confirm the change.
"""

    def _build(self) -> None:
        ttk.Label(self, text="Increase or decrease audio volume by dB 🔊", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._db = _LabeledEntry(r2, "Volume (dB)", "6.0")
        self._db.pack(fill="x", expand=True)

        r3 = self._row()
        self._out = _FileEntry(r3, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="🔊  Adjust Volume", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an input file.", "error")
            return
        try:
            db = float(self._db.value)
        except ValueError:
            self._log("Volume must be a number.", "error")
            return
        out = self._out.value or None
        self._log(f"Adjusting volume of {path!r} by {db:+.1f} dB …", "info")
        def task() -> None:
            try:
                from musicprod.tools.volume_adjuster import adjust_volume
                result = adjust_volume(path, db=db, output_path=out)
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _CompressorPanel(_ToolPanel):
    title = "Audio Compressor"
    icon = "📦"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Applies dynamic range compression: reduces the volume of loud
passages so quiet and loud sections sound more even.

PARAMETERS
─────────────────────────────────────────────────────
• Input file — The audio file to compress.
• Threshold (dBFS) — The volume level above which compression begins.
  Louder-than-threshold audio is turned down.
  Default: -20.0 dBFS. More negative = compression starts earlier.
• Ratio (e.g. 4.0) — How much loud audio is reduced.
  4.0 = 4:1 ratio: for every 4 dB above threshold, only 1 dB passes.
  Higher ratio = heavier compression. ∞:1 = limiting (hard ceiling).
  Typical range: 2.0–8.0.
• Attack (ms) — How quickly the compressor kicks in after audio
  exceeds the threshold. Shorter = faster response.
  Default: 5 ms. Range: 1–100 ms.
• Release (ms) — How quickly the compressor stops after audio falls
  below the threshold. Shorter = snappier feel.
  Default: 50 ms. Range: 10–500 ms.
• Output file (opt.) — Where to save the result.

TIPS & TRICKS
─────────────────────────────────────────────────────
• Start gentle: Threshold -20, Ratio 3:1, Attack 10 ms, Release 60 ms.
• Heavy compression (Ratio ≥ 8:1) starts acting like a limiter.
• Fast attack can reduce transient punch (e.g. on drums).
  Slow attack lets transients through for a punchier feel.
• After compressing, raise overall volume with the Volume Adjuster
  to make up for the gained headroom ("make-up gain").
• Compression is fundamental in podcasting, broadcast, and mastering.
"""

    def _build(self) -> None:
        ttk.Label(self, text="Apply dynamic range compression to audio 📦", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._thresh = _LabeledEntry(r2, "Threshold (dBFS)", "-20.0")
        self._thresh.pack(fill="x", expand=True)

        r3 = self._row()
        self._ratio = _LabeledEntry(r3, "Ratio (e.g. 4.0)", "4.0")
        self._ratio.pack(fill="x", expand=True)

        r4 = self._row()
        self._attack = _LabeledEntry(r4, "Attack (ms)", "5.0")
        self._attack.pack(fill="x", expand=True)

        r5 = self._row()
        self._release = _LabeledEntry(r5, "Release (ms)", "50.0")
        self._release.pack(fill="x", expand=True)

        r6 = self._row()
        self._out = _FileEntry(r6, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="📦  Compress", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an input file.", "error")
            return
        try:
            thresh = float(self._thresh.value)
            ratio = float(self._ratio.value)
            attack = float(self._attack.value)
            release = float(self._release.value)
        except ValueError:
            self._log("All compression parameters must be numbers.", "error")
            return
        out = self._out.value or None
        self._log(f"Compressing {path!r} (threshold={thresh} dBFS, ratio={ratio}:1) …", "info")
        def task() -> None:
            try:
                from musicprod.tools.audio_compressor import compress_audio
                result = compress_audio(path, threshold=thresh, ratio=ratio,
                                        attack=attack, release=release, output_path=out)
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


class _LoopPanel(_ToolPanel):
    title = "Loop Creator"
    icon = "🔁"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Repeats an audio file a specified number of times to create a longer
looped version. Optionally applies a crossfade at each loop point
for a seamless transition.

PARAMETERS
─────────────────────────────────────────────────────
• Input file — The audio file to loop.
• Repeat count — How many times to play the audio in total.
  2 = play it twice (original + 1 repeat), 4 = four times, etc.
• Crossfade (ms) — Duration of the fade overlap at each loop join in
  milliseconds. 0 = hard cut (no crossfade).
  Use crossfade to smooth seamless loops.
• Output file (opt.) — Where to save the result.

TIPS & TRICKS
─────────────────────────────────────────────────────
• For a truly seamless loop, make sure the audio is already loop-ready
  (the end naturally flows into the beginning — same note, no tail).
• Add a short crossfade (50–200 ms) to mask small discontinuities at
  the loop point.
• Longer crossfades (500+ ms) can create a "blending" effect, useful
  for ambient textures and background music.
• Combine with the Fade Effect (fade out the final iteration) to
  create a naturally ending looped track.
• Common use cases: background music for videos, game audio, ringtones,
  music beds for podcasts.
"""

    def _build(self) -> None:
        ttk.Label(self, text="Repeat audio N times to create a loop 🔁", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._count = _LabeledEntry(r2, "Repeat count", "4")
        self._count.pack(fill="x", expand=True)

        r3 = self._row()
        self._xfade = _LabeledEntry(r3, "Crossfade (ms)", "0")
        self._xfade.pack(fill="x", expand=True)

        r4 = self._row()
        self._out = _FileEntry(r4, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="🔁  Create Loop", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an input file.", "error")
            return
        try:
            count = int(self._count.value)
            xfade = int(self._xfade.value)
        except ValueError:
            self._log("Count and crossfade must be integers.", "error")
            return
        out = self._out.value or None
        self._log(f"Creating {count}× loop of {path!r} …", "info")
        def task() -> None:
            try:
                from musicprod.tools.loop_creator import create_loop
                result = create_loop(path, count=count, crossfade=xfade, output_path=out)
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")
        self._run_in_thread(task)


# ---------------------------------------------------------------------------
# Vocal Auto-Tune panel
# ---------------------------------------------------------------------------

_AUTOTUNE_SCALES = [
    "chromatic",
    "C major", "C# major", "D major", "D# major", "E major",
    "F major", "F# major", "G major", "G# major", "A major", "A# major", "B major",
    "C minor", "C# minor", "D minor", "D# minor", "E minor",
    "F minor", "F# minor", "G minor", "G# minor", "A minor", "A# minor", "B minor",
]


class _AutotunePanel(_ToolPanel):
    title = "Vocal Auto-Tune"
    icon = "🎤"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Corrects the pitch of a vocal recording by snapping each note to the
nearest note in a chosen musical scale. The algorithm:
  1. Detects the pitch of each voiced segment using PYIN (a probabilistic
     fundamental-frequency estimator designed for singing voices).
  2. Finds the closest note in the target scale.
  3. Shifts that segment's pitch by the difference, scaled by the
     Correction strength.

PARAMETERS
─────────────────────────────────────────────────────
• Input file — The vocal (or any pitched) audio file.
• Scale — The musical scale to snap to.
  "chromatic" snaps to the nearest semitone regardless of key, which
  is useful for cleaning up slightly off-pitch notes without imposing
  a key. Selecting a specific key/mode (e.g. "C major", "A minor")
  confines corrections to only the notes of that scale.
• Correction strength (0.0–1.0) — How far to move each note towards
  the target:
    1.0  Full correction — classic robotic auto-tune effect.
    0.5  Half correction — subtle pitch assist.
    0.0  No correction — passes audio unchanged.
• Output file (opt.) — Where to save the result. MP3 inputs are
  automatically saved as .wav (MP3 write requires FFmpeg post-process).

TIPS & TRICKS
─────────────────────────────────────────────────────
• Use the Key Detector tool first to find the song's key, then set
  the Scale here to match — this gives the most musical results.
• Strength 0.8–1.0 → obvious, modern pop auto-tune effect.
• Strength 0.3–0.6 → transparent pitch correction (almost undetectable).
• "Chromatic" is good for melodic instruments (guitar, flute); a
  specific key scale sounds more natural for vocals.
• Best results come from clean, single-voice recordings (no backing
  track, no heavy reverb). Heavy reverb can confuse pitch detection.
• Very fast melisma (rapid note runs) may not correct cleanly because
  the algorithm averages pitch over a short window. Use a lower
  strength in those cases.
• The output is always mono. If you need stereo output, apply auto-tune
  to each channel separately and merge with the Audio Merger tool.
"""

    def _build(self) -> None:
        ttk.Label(
            self,
            text="Correct vocal pitch to the nearest scale note 🎤",
            style="Muted.TLabel",
        ).pack(anchor="w", padx=16, pady=(12, 8))

        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        ttk.Label(r2, text="Scale", style="Muted.TLabel", width=18, anchor="w").pack(side="left")
        self._scale = ttk.Combobox(r2, values=_AUTOTUNE_SCALES, state="readonly", width=16)
        self._scale.set("chromatic")
        self._scale.pack(side="left")

        r3 = self._row()
        self._strength = _LabeledEntry(r3, "Correction (0–1)", "1.0")
        self._strength.pack(fill="x", expand=True)

        r4 = self._row()
        self._out = _FileEntry(r4, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="🎤  Auto-Tune", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an input file.", "error")
            return
        try:
            strength = float(self._strength.value)
        except ValueError:
            self._log("Correction strength must be a number between 0.0 and 1.0.", "error")
            return
        scale = self._scale.get()
        out = self._out.value or None
        self._log(
            f"Auto-tuning {path!r} to scale {scale!r} (strength={strength:.2f}) …",
            "info",
        )

        def task() -> None:
            try:
                from musicprod.tools.vocal_autotune import autotune_vocals
                result = autotune_vocals(
                    path, scale=scale, correction_strength=strength, output_path=out
                )
                self._log(f"Saved: {result}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")

        self._run_in_thread(task)


# ---------------------------------------------------------------------------
# Chord Detector panel
# ---------------------------------------------------------------------------

class _ChordPanel(_ToolPanel):
    title = "Chord Detector"
    icon = "🎼"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Analyses the harmonic content of an audio file and detects which chord
is being played at each moment, producing a full chord progression.

The detection uses a CQT-based chromagram combined with template
matching against all 24 major and minor triads (C, Cm, C#, C#m, …).

PARAMETERS
─────────────────────────────────────────────────────
• Audio file — Any common audio format (MP3, WAV, FLAC, OGG …).
• Frame size (samples) — Size of each analysis window.
  Larger = smoother chord boundaries but less time resolution.
  Default: 4096 (~93 ms at 44.1 kHz). Try 2048 for faster songs.
• Min duration (s) — Chord segments shorter than this are merged into
  their neighbour to reduce detection noise. Default: 0.5 s.
• Output text file (opt.) — Save the chord list to a plain-text file.
  Leave blank to view results only in the log below.

TIPS & TRICKS
─────────────────────────────────────────────────────
• Results are most accurate for recordings with clear harmonic content
  (piano, guitar, clear vocals). Dense mixes or heavy distortion may
  reduce accuracy.
• If you see many fast chord changes, increase Min duration (e.g. 1.0)
  to get a cleaner, more musical result.
• Chord names use standard notation:
    C   = C major (C, E, G)
    Cm  = C minor (C, Eb, G)
    C#  = C# major / Db major
    C#m = C# minor / Db minor
• Use the detected chords together with the Key Detector result to
  understand the harmonic structure and find compatible songs.
• The chord list can be used for transcription, cover versions,
  remixing, or studying music theory.
• Save to a text file to copy chord symbols into your DAW, sheet music
  software, or share with other musicians.
"""

    def _build(self) -> None:
        ttk.Label(
            self,
            text="Detect chord progression from an audio file 🎼",
            style="Muted.TLabel",
        ).pack(anchor="w", padx=16, pady=(12, 8))

        r1 = self._row()
        self._file = _FileEntry(r1, "Audio file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._hop_length = _LabeledEntry(r2, "Frame size (samples)", "4096")
        self._hop_length.pack(fill="x", expand=True)

        r3 = self._row()
        self._min_dur = _LabeledEntry(r3, "Min duration (s)", "0.5")
        self._min_dur.pack(fill="x", expand=True)

        r4 = self._row()
        self._out = _FileEntry(
            r4,
            "Output text file (opt.)",
            mode="save",
            filetypes=[("Text file", "*.txt"), ("All files", "*.*")],
        )
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="🎼  Detect Chords", command=self._run, style="Accent.TButton").pack(pady=12)

    def _run(self) -> None:
        path = self._file.value
        if not path:
            self._log("Please select an audio file.", "error")
            return
        try:
            hop = int(self._hop_length.value)
            min_dur = float(self._min_dur.value)
        except ValueError:
            self._log("Frame size must be an integer and min duration a number.", "error")
            return
        out = self._out.value or None
        self._log(f"Analysing chords in {path!r} …", "info")

        def task() -> None:
            try:
                from musicprod.tools.chord_detector import detect_chords, format_chords
                segments = detect_chords(path, hop_length=hop, min_duration=min_dur, output_path=out)
                if not segments:
                    self._log("No chords detected.", "info")
                    return
                self._log(f"Detected {len(segments)} chord segment(s):", "success")
                for line in format_chords(segments).splitlines():
                    self._log(line, "info")
                if out:
                    self._log(f"Saved: {out}", "success")
            except Exception as exc:
                self._log(f"Error: {exc}", "error")

        self._run_in_thread(task)


# ---------------------------------------------------------------------------
# Update panel
# ---------------------------------------------------------------------------

class _UpdatePanel(_ToolPanel):
    title = "Update"
    icon = "🔃"
    help_text = """\
WHAT THIS TOOL DOES
─────────────────────────────────────────────────────
Checks whether a newer version of MusicProd is available and
upgrades the installation automatically.

HOW IT WORKS
─────────────────────────────────────────────────────
• If MusicProd was installed by cloning the Git repository, the
  updater runs "git pull" to fetch and apply the latest commits.
• If MusicProd was installed via pip, the updater runs
  "pip install --upgrade musicprod" to install the newest release.

TIPS & TRICKS
─────────────────────────────────────────────────────
• Run the update from time to time to get new tools, bug fixes,
  and performance improvements.
• A working internet connection is required.
• If the update fails, try updating manually:
    Via git:  git pull origin main
    Via pip:  pip install --upgrade musicprod
• After a successful update, restart MusicProd Hub to load any
  new or changed tool panels.
• If you modified local files (e.g. settings), a git pull may report
  conflicts — resolve them in the terminal before re-running.
"""

    def _build(self) -> None:
        ttk.Label(
            self,
            text="Update MusicProd to the latest version from main 🌸",
            style="Muted.TLabel",
        ).pack(anchor="w", padx=16, pady=(12, 8))

        ttk.Button(
            self, text="🔃  Check for Updates", command=self._run, style="Accent.TButton"
        ).pack(pady=(12, 4))

        ttk.Button(
            self, text="🔄  Restart Hub", command=self._restart_hub, style="Small.TButton"
        ).pack(pady=(0, 12))

    def _restart_hub(self) -> None:
        """Restart MusicProd Hub to apply any installed updates."""
        try:
            subprocess.Popen([sys.executable] + sys.argv)  # noqa: S603
        except Exception as exc:  # pragma: no cover
            self._log(f"Restart failed: {exc}", "error")
            return
        self.winfo_toplevel().destroy()

    def _run(self) -> None:
        self._log("Checking for updates…", "info")

        def task() -> None:
            try:
                from musicprod.tools.updater import self_update

                method, message = self_update()
                label = "git pull" if method == "git" else "pip upgrade"
                self._log(f"[{label}] {message}", "success")
                self._log(
                    "➡  Restart MusicProd Hub to load the new version"
                    " (click the Restart Hub button above).",
                    "info",
                )
            except Exception as exc:
                self._log(f"Update failed: {exc}", "error")

        self._run_in_thread(task)


# ---------------------------------------------------------------------------
# Main Hub window
# ---------------------------------------------------------------------------

_PANELS: list[type[_ToolPanel]] = [
    _YouTubePanel,
    _BPMPanel,
    _FormatPanel,
    _TrimPanel,
    _MetadataPanel,
    _NormalizePanel,
    _PitchPanel,
    _SplitPanel,
    _MergePanel,
    _WaveformPanel,
    _NoiseReducerPanel,
    _FadePanel,
    _SilenceRemoverPanel,
    _ChannelPanel,
    _TempoPanel,
    _ReverbPanel,
    _KeyDetectorPanel,
    _VolumePanel,
    _CompressorPanel,
    _LoopPanel,
    _AutotunePanel,
    _ChordPanel,
    _UpdatePanel,
]


class MusicProdHub(tk.Tk):
    """The MusicProd Hub main window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("MusicProd Hub")
        self.geometry("960x640")
        self.minsize(780, 500)
        self.configure(bg=DARK_BG)
        self._setup_styles()
        self._build_ui()
        self._select_tool(0)

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".", background=DARK_BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("TFrame", background=DARK_BG)
        style.configure("Card.TFrame", background=CARD_BG)
        style.configure("Sidebar.TFrame", background=SIDEBAR_BG)

        style.configure("TLabel", background=DARK_BG, foreground=TEXT)
        style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT)
        style.configure("Muted.TLabel", background=CARD_BG, foreground=MUTED)
        style.configure("Header.TLabel", background=SIDEBAR_BG, foreground=ACCENT,
                        font=("Segoe UI", 11, "bold"))
        style.configure("Title.TLabel", background=DARK_BG, foreground=ACCENT,
                        font=("Segoe UI", 17, "bold"))
        style.configure("Subtitle.TLabel", background=DARK_BG, foreground=MUTED,
                        font=("Segoe UI", 9))

        style.configure("Accent.TButton",
                        background=ACCENT, foreground="#ffffff",
                        font=("Segoe UI", 10, "bold"),
                        padding=(12, 6), borderwidth=0, relief="flat")
        style.map("Accent.TButton",
                  background=[("active", ACCENT_HOVER)],
                  foreground=[("active", "#ffffff")])

        style.configure("Small.TButton",
                        background=ENTRY_BG, foreground=TEXT,
                        font=("Segoe UI", 9), padding=(6, 3), borderwidth=0)
        style.map("Small.TButton",
                  background=[("active", ACCENT)],
                  foreground=[("active", "#ffffff")])

        style.configure("SidebarTool.TButton",
                        background=SIDEBAR_BG, foreground=TEXT,
                        anchor="w", font=("Segoe UI", 10),
                        padding=(12, 8), borderwidth=0, relief="flat")
        style.map("SidebarTool.TButton",
                  background=[("active", CARD_BG)],
                  foreground=[("active", ACCENT)])

        style.configure("ActiveSidebarTool.TButton",
                        background=CARD_BG, foreground=ACCENT,
                        anchor="w", font=("Segoe UI", 10, "bold"),
                        padding=(12, 8), borderwidth=0, relief="flat")

        style.configure("Dark.TEntry",
                        fieldbackground=ENTRY_BG, foreground=TEXT,
                        insertcolor=TEXT, borderwidth=0, padding=5)
        style.map("Dark.TEntry", fieldbackground=[("focus", "#ffc0d9")])

        style.configure("TCombobox",
                        fieldbackground=ENTRY_BG, foreground=TEXT,
                        background=ENTRY_BG, arrowcolor=ACCENT,
                        selectbackground=ACCENT, selectforeground="#ffffff")
        self.option_add("*TCombobox*Listbox.background", CARD_BG)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)

        # Separator colour
        style.configure("TSeparator", background="#ffadd4")

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ── Header ──────────────────────────────────────────────────────
        header = ttk.Frame(self)
        header.pack(fill="x", padx=0, pady=0)
        ttk.Label(header, text="🌸  MusicProd Hub  🌸", style="Title.TLabel",
                  padding=(20, 12, 0, 4)).pack(side="left")
        ttk.Label(header, text="22 tools — one place ✨",
                  style="Subtitle.TLabel", padding=(8, 12, 0, 4)).pack(side="left", anchor="s")

        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # ── Body (sidebar + main panel) ─────────────────────────────────
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        # Sidebar (scrollable)
        sidebar_outer = ttk.Frame(body, style="Sidebar.TFrame", width=200)
        sidebar_outer.pack(side="left", fill="y")
        sidebar_outer.pack_propagate(False)

        ttk.Label(sidebar_outer, text="🎀 TOOLS 🎀", style="Header.TLabel",
                  padding=(12, 10, 0, 4)).pack(anchor="w")

        # Canvas + scrollbar for scrollable tool list
        sidebar_canvas = tk.Canvas(
            sidebar_outer,
            bg=SIDEBAR_BG,
            highlightthickness=0,
            borderwidth=0,
        )
        sidebar_scrollbar = ttk.Scrollbar(
            sidebar_outer, orient="vertical", command=sidebar_canvas.yview
        )
        sidebar_canvas.configure(yscrollcommand=sidebar_scrollbar.set)

        sidebar_scrollbar.pack(side="right", fill="y")
        sidebar_canvas.pack(side="left", fill="both", expand=True)

        sidebar = ttk.Frame(sidebar_canvas, style="Sidebar.TFrame")
        sidebar_window = sidebar_canvas.create_window(
            (0, 0), window=sidebar, anchor="nw"
        )

        def _on_sidebar_configure(_event: tk.Event) -> None:
            sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all"))

        def _on_canvas_resize(event: tk.Event) -> None:
            if hasattr(event, "width") and event.width > 0:
                sidebar_canvas.itemconfig(sidebar_window, width=event.width)

        sidebar.bind("<Configure>", _on_sidebar_configure)
        sidebar_canvas.bind("<Configure>", _on_canvas_resize)

        def _on_mousewheel(event: tk.Event) -> None:
            # Cross-platform mouse wheel scrolling
            if event.num == 4:
                sidebar_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                sidebar_canvas.yview_scroll(1, "units")
            else:
                # event.delta is 120-per-notch on Windows; on macOS it can be
                # much smaller (±1). Use int(…) or 1 so we always scroll at
                # least one unit.
                delta = int(-1 * (event.delta / 120)) or (-1 if event.delta > 0 else 1)
                sidebar_canvas.yview_scroll(delta, "units")

        sidebar_canvas.bind("<MouseWheel>", _on_mousewheel)
        sidebar_canvas.bind("<Button-4>", _on_mousewheel)
        sidebar_canvas.bind("<Button-5>", _on_mousewheel)
        sidebar.bind("<MouseWheel>", _on_mousewheel)
        sidebar.bind("<Button-4>", _on_mousewheel)
        sidebar.bind("<Button-5>", _on_mousewheel)

        self._sidebar_buttons: list[ttk.Button] = []
        for i, panel_cls in enumerate(_PANELS):
            btn = ttk.Button(
                sidebar,
                text=f"  {panel_cls.icon}  {panel_cls.title}",
                style="SidebarTool.TButton",
                command=lambda idx=i: self._select_tool(idx),
            )
            btn.pack(fill="x", pady=1)
            btn.bind("<MouseWheel>", _on_mousewheel)
            btn.bind("<Button-4>", _on_mousewheel)
            btn.bind("<Button-5>", _on_mousewheel)
            self._sidebar_buttons.append(btn)

        ttk.Separator(body, orient="vertical").pack(side="left", fill="y")

        # Main panel container
        self._main = ttk.Frame(body, style="Card.TFrame")
        self._main.pack(side="left", fill="both", expand=True)

        # ── Log / status area ───────────────────────────────────────────
        ttk.Separator(self, orient="horizontal").pack(fill="x")
        log_frame = ttk.Frame(self)
        log_frame.pack(fill="x")
        ttk.Label(log_frame, text="✨ Output", style="Muted.TLabel",
                  padding=(8, 4, 0, 0)).pack(anchor="w")
        self._log_box = scrolledtext.ScrolledText(
            log_frame, height=6, wrap="word",
            bg=SIDEBAR_BG, fg=TEXT, insertbackground=ACCENT,
            font=("Courier New", 9), relief="flat", bd=0,
        )
        self._log_box.pack(fill="x", padx=8, pady=(0, 8))
        self._log_box.tag_config("error", foreground=ERROR_COLOR)
        self._log_box.tag_config("success", foreground=SUCCESS_COLOR)
        self._log_box.tag_config("info", foreground=TEXT)
        self._log_box.configure(state="disabled")

        # Build all panels (hidden initially)
        self._panels: list[_ToolPanel] = []
        for panel_cls in _PANELS:
            panel = panel_cls(self._main, self._log)
            panel.place(relwidth=1, relheight=1)
            self._panels.append(panel)

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def _select_tool(self, index: int) -> None:
        for i, btn in enumerate(self._sidebar_buttons):
            btn.configure(style="ActiveSidebarTool.TButton" if i == index else "SidebarTool.TButton")
        self._panels[index].lift()

    def _log(self, message: str, level: str = "info") -> None:
        """Append *message* to the log box (thread-safe)."""
        def _append() -> None:
            self._log_box.configure(state="normal")
            self._log_box.insert("end", message + "\n", level)
            self._log_box.see("end")
            self._log_box.configure(state="disabled")
        self.after(0, _append)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Launch the MusicProd Hub GUI."""
    app = MusicProdHub()
    app.mainloop()


if __name__ == "__main__":
    main()
