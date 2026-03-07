"""MusicProd Hub — Tkinter GUI giving access to all 10 music production tools."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, scrolledtext, ttk
from typing import Callable

# ---------------------------------------------------------------------------
# Colour palette (dark, Spotify-inspired)
# ---------------------------------------------------------------------------
DARK_BG = "#1e1e2e"
CARD_BG = "#2a2a3e"
SIDEBAR_BG = "#181825"
ACCENT = "#1DB954"
ACCENT_HOVER = "#17a349"
TEXT = "#cdd6f4"
MUTED = "#6c7086"
ERROR_COLOR = "#f38ba8"
SUCCESS_COLOR = "#a6e3a1"
ENTRY_BG = "#313244"


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
    icon = "▶"

    def _build(self) -> None:
        ttk.Label(self, text="Download audio from YouTube as MP3", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        ttk.Label(r1, text="YouTube URL", style="Muted.TLabel", width=18, anchor="w").pack(side="left")
        self._url = tk.StringVar()
        ttk.Entry(r1, textvariable=self._url, style="Dark.TEntry").pack(side="left", fill="x", expand=True)

        r2 = self._row()
        self._out = _FileEntry(r2, "Output file (.mp3)", mode="save", filetypes=[("MP3", "*.mp3"), ("All files", "*.*")])
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="⬇  Download", command=self._run, style="Accent.TButton").pack(pady=12)

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
    icon = "♩"

    def _build(self) -> None:
        ttk.Label(self, text="Detect the tempo (BPM) of an audio file", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Audio file")
        self._file.pack(fill="x", expand=True)
        ttk.Button(self, text="♩  Detect BPM", command=self._run, style="Accent.TButton").pack(pady=12)

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
    icon = "⇄"

    def _build(self) -> None:
        ttk.Label(self, text="Convert audio between formats (MP3, WAV, FLAC, OGG …)", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
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

        ttk.Button(self, text="⇄  Convert", command=self._run, style="Accent.TButton").pack(pady=12)

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
    icon = "✂"

    def _build(self) -> None:
        ttk.Label(self, text="Trim an audio file to a start/end timestamp", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
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

        ttk.Button(self, text="✂  Trim", command=self._run, style="Accent.TButton").pack(pady=12)

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
    icon = "🏷"

    def _build(self) -> None:
        ttk.Label(self, text="View or edit audio file metadata tags", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
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
    icon = "◈"

    def _build(self) -> None:
        ttk.Label(self, text="Normalize audio loudness to a target dBFS level", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._dbfs = _LabeledEntry(r2, "Target dBFS", "-14.0")
        self._dbfs.pack(fill="x", expand=True)

        r3 = self._row()
        self._out = _FileEntry(r3, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="◈  Normalize", command=self._run, style="Accent.TButton").pack(pady=12)

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
    icon = "♫"

    def _build(self) -> None:
        ttk.Label(self, text="Shift the pitch of an audio file by semitones", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._semi = _LabeledEntry(r2, "Semitones", "2")
        self._semi.pack(fill="x", expand=True)

        r3 = self._row()
        self._out = _FileEntry(r3, "Output file (opt.)", mode="save")
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="♫  Shift Pitch", command=self._run, style="Accent.TButton").pack(pady=12)

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
    icon = "⊞"

    def _build(self) -> None:
        ttk.Label(self, text="Split an audio file into equal-duration chunks", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._dur = _LabeledEntry(r2, "Chunk duration (s)", "30")
        self._dur.pack(fill="x", expand=True)

        r3 = self._row()
        self._outdir = _FileEntry(r3, "Output dir (opt.)", mode="dir")
        self._outdir.pack(fill="x", expand=True)

        ttk.Button(self, text="⊞  Split", command=self._run, style="Accent.TButton").pack(pady=12)

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
    icon = "⊕"

    def __init__(self, master: tk.Widget, log: Callable[[str, str], None]) -> None:
        self._file_entries: list[_FileEntry] = []
        super().__init__(master, log)

    def _build(self) -> None:
        ttk.Label(self, text="Merge/concatenate multiple audio files into one", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))

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

        ttk.Button(self, text="⊕  Merge", command=self._run, style="Accent.TButton").pack(pady=12)

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
    icon = "〜"

    def _build(self) -> None:
        ttk.Label(self, text="Generate a waveform PNG image of an audio file", style="Muted.TLabel").pack(anchor="w", padx=16, pady=(12, 8))
        r1 = self._row()
        self._file = _FileEntry(r1, "Input file")
        self._file.pack(fill="x", expand=True)

        r2 = self._row()
        self._out = _FileEntry(r2, "Output PNG (opt.)", mode="save", filetypes=[("PNG image", "*.png"), ("All files", "*.*")])
        self._out.pack(fill="x", expand=True)

        ttk.Button(self, text="〜  Plot Waveform", command=self._run, style="Accent.TButton").pack(pady=12)

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
        style.configure("Header.TLabel", background=SIDEBAR_BG, foreground=TEXT, font=("Segoe UI", 12, "bold"))
        style.configure("Title.TLabel", background=DARK_BG, foreground=TEXT, font=("Segoe UI", 16, "bold"))
        style.configure("Subtitle.TLabel", background=DARK_BG, foreground=MUTED, font=("Segoe UI", 9))

        style.configure("Accent.TButton",
                        background=ACCENT, foreground="#000000",
                        font=("Segoe UI", 10, "bold"),
                        padding=(10, 5), borderwidth=0)
        style.map("Accent.TButton",
                  background=[("active", ACCENT_HOVER)],
                  foreground=[("active", "#000000")])

        style.configure("Small.TButton",
                        background=ENTRY_BG, foreground=TEXT,
                        font=("Segoe UI", 9), padding=(6, 3), borderwidth=0)
        style.map("Small.TButton", background=[("active", "#44475a")])

        style.configure("SidebarTool.TButton",
                        background=SIDEBAR_BG, foreground=TEXT,
                        anchor="w", font=("Segoe UI", 10),
                        padding=(12, 8), borderwidth=0, relief="flat")
        style.map("SidebarTool.TButton",
                  background=[("active", CARD_BG), ("selected", CARD_BG)],
                  foreground=[("active", ACCENT)])

        style.configure("ActiveSidebarTool.TButton",
                        background=CARD_BG, foreground=ACCENT,
                        anchor="w", font=("Segoe UI", 10, "bold"),
                        padding=(12, 8), borderwidth=0, relief="flat")

        style.configure("Dark.TEntry",
                        fieldbackground=ENTRY_BG, foreground=TEXT,
                        insertcolor=TEXT, borderwidth=0, padding=5)
        style.map("Dark.TEntry", fieldbackground=[("focus", "#3d3f5a")])

        style.configure("TCombobox",
                        fieldbackground=ENTRY_BG, foreground=TEXT,
                        background=ENTRY_BG, arrowcolor=TEXT,
                        selectbackground=ACCENT, selectforeground="#000000")
        self.option_add("*TCombobox*Listbox.background", CARD_BG)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ── Header ──────────────────────────────────────────────────────
        header = ttk.Frame(self)
        header.pack(fill="x", padx=0, pady=0)
        ttk.Label(header, text="🎵  MusicProd Hub", style="Title.TLabel",
                  padding=(20, 12, 0, 4)).pack(side="left")
        ttk.Label(header, text="10 tools — one place",
                  style="Subtitle.TLabel", padding=(8, 12, 0, 4)).pack(side="left", anchor="s")

        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # ── Body (sidebar + main panel) ─────────────────────────────────
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        # Sidebar
        sidebar = ttk.Frame(body, style="Sidebar.TFrame", width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ttk.Label(sidebar, text="TOOLS", style="Header.TLabel",
                  padding=(12, 10, 0, 4)).pack(anchor="w")

        self._sidebar_buttons: list[ttk.Button] = []
        for i, panel_cls in enumerate(_PANELS):
            btn = ttk.Button(
                sidebar,
                text=f"  {panel_cls.icon}  {panel_cls.title}",
                style="SidebarTool.TButton",
                command=lambda idx=i: self._select_tool(idx),
            )
            btn.pack(fill="x", pady=1)
            self._sidebar_buttons.append(btn)

        ttk.Separator(body, orient="vertical").pack(side="left", fill="y")

        # Main panel container
        self._main = ttk.Frame(body, style="Card.TFrame")
        self._main.pack(side="left", fill="both", expand=True)

        # ── Log / status area ───────────────────────────────────────────
        ttk.Separator(self, orient="horizontal").pack(fill="x")
        log_frame = ttk.Frame(self)
        log_frame.pack(fill="x")
        ttk.Label(log_frame, text="Output", style="Muted.TLabel",
                  padding=(8, 4, 0, 0)).pack(anchor="w")
        self._log_box = scrolledtext.ScrolledText(
            log_frame, height=6, wrap="word",
            bg=SIDEBAR_BG, fg=TEXT, insertbackground=TEXT,
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
