"""MusicProd Hub — Tkinter GUI giving access to all 20 music production tools."""

from __future__ import annotations

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

    def __init__(self, master: tk.Widget, log: Callable[[str, str], None]) -> None:
        super().__init__(master, style="Card.TFrame")
        self._log = log
        self._build()

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
        ttk.Label(header, text="20 tools — one place ✨",
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
