# MusicProd Tools 🎵

A collection of command-line tools **and a graphical hub** for music production, built in Python.

---

## 🪟 Windows Users — Get the EXE (no Python required)

> **The `.exe` file is NOT included in the repository source code.**  
> It is built automatically and published to **GitHub Releases** whenever a new version is tagged.

### How to download and run

1. Go to the [**Releases page**](https://github.com/AMix-hub/musicprod/releases/latest).
2. Under **Assets**, click **`musicprod-hub.exe`** to download it.
3. Double-click the downloaded file — no installation needed.

If you cloned or downloaded the repository as a ZIP, you will **not** find the `.exe` inside it.  
You must download the pre-built binary from the Releases page as described above.

#### Building the EXE yourself (optional)

If you prefer to build the executable from source:

```bash
# 1. Install the package and PyInstaller
pip install -e .
pip install pyinstaller

# 2. Build the executable (output: dist/musicprod-hub.exe)
pyinstaller musicprod-hub.spec
```

---

## 10 Music Production Tools

| # | Tool | CLI Command | Description |
|---|------|-------------|-------------|
| 1 | **YouTube → MP3** | `youtube-to-mp3` | Download audio from YouTube links and save as MP3 files |
| 2 | **BPM Detector** | `detect-bpm` | Analyse an audio file and detect its tempo (BPM) |
| 3 | **Audio Format Converter** | `convert-format` | Convert between audio formats (MP3, WAV, FLAC, OGG, AAC …) |
| 4 | **Audio Trimmer** | `trim-audio` | Trim an audio file to a specific start/end timestamp |
| 5 | **Metadata Editor** | `edit-metadata` | View and edit ID3/audio metadata tags (artist, title, album …) |
| 6 | **Audio Normalizer** | `normalize-audio` | Normalize loudness to a target dBFS level |
| 7 | **Pitch Shifter** | `shift-pitch` | Shift pitch up or down by any number of semitones |
| 8 | **Audio Splitter** | `split-audio` | Split an audio file into equal-duration chunks |
| 9 | **Audio Merger** | `merge-audio` | Concatenate multiple audio files into one |
| 10 | **Waveform Plotter** | `plot-waveform` | Generate a dark-themed waveform PNG image |

All tools are available via the **CLI** (`musicprod <command>`) **and** the **graphical Hub** (`musicprod hub` / `musicprod-hub`).

---

## MusicProd Hub (GUI)

Launch the graphical hub to access all 10 tools with file browsers and a live output log:

```bash
musicprod hub
# or equivalently:
musicprod-hub
```

![MusicProd Hub screenshot](https://github.com/user-attachments/assets/4c825c5f-7ae8-4086-9ac0-0e0a10219137)

The hub provides:
- **Sidebar** listing all 10 tools — click to switch instantly
- **File browser** buttons on every tool panel
- **Live output log** at the bottom showing success/error messages
- Runs tool operations in background threads so the UI stays responsive

> **Requirements:** a desktop display (X11/Wayland/macOS/Windows) and Python's built-in `tkinter`.  
> On headless servers use the CLI commands instead.

---

## Windows — Standalone EXE 🪟

See the [**Windows Users section at the top**](#-windows-users--get-the-exe-no-python-required) for download instructions.

### Updating the EXE

The Hub has a built-in one-click updater on the **Update** tab:

1. Open MusicProd Hub.
2. Click **🔃 Check for Updates** — the hub contacts GitHub Releases,
   downloads the new `musicprod-hub.exe` in the background, and confirms
   in the output log when the download is complete.
3. Click **🔄 Restart Hub** — the new binary launches and the old one exits.

That's it.  No manual file management needed.

---

## Updating MusicProd

When a new version is pushed to `main` you don't need to re-download or
re-install the whole project.  Just run:

```bash
musicprod update
```

The command automatically detects how the package is installed:

- **Windows EXE** — downloads the latest `musicprod-hub.exe` from GitHub
  Releases and prompts you to restart.
- **Git clone (editable install)** — runs `git pull --ff-only` inside the
  repository directory.  Because the package is installed with
  `pip install -e .`, the updated code is active immediately — no reinstall
  needed.
- **Regular pip install** — upgrades the package from the GitHub repository
  with `pip install --upgrade git+https://github.com/AMix-hub/musicprod.git`.

After any update, **restart MusicProd Hub** (or click the **🔄 Restart Hub**
button) so the new code is loaded.

---

## Quick Start

Follow these steps to go from a fresh clone to running commands in under five minutes.

### 1. Install FFmpeg

FFmpeg is required by the format-converter, audio-trimmer, normalizer, splitter and merger tools.

```bash
# macOS (Homebrew)
brew install ffmpeg

# Ubuntu / Debian
sudo apt-get update && sudo apt-get install -y ffmpeg

# Windows (Chocolatey)
choco install ffmpeg
```

> Confirm it works: `ffmpeg -version`

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Install musicprod with dev dependencies

```bash
pip install -e ".[dev]"
```

### 4. Verify the installation

```bash
musicprod --help
```

You should see all ten tools listed.

### 5. Run the test suite

```bash
pytest -v
```

All tests run without needing real audio files or a live internet connection — everything is mocked.

---

## Requirements

- Python 3.9+
- [FFmpeg](https://ffmpeg.org/download.html) installed and on your `PATH`
- `tkinter` (Python built-in; on Ubuntu/Debian: `sudo apt-get install python3-tk`)

## Installation

```bash
pip install -e .
```

Or install only the runtime dependencies:

```bash
pip install -r requirements.txt
```

## Usage

All tools are available through the `musicprod` CLI:

```
musicprod --help
```

### Tool 1 — YouTube → MP3

```bash
musicprod youtube-to-mp3 "https://www.youtube.com/watch?v=<ID>"
musicprod youtube-to-mp3 "https://www.youtube.com/watch?v=<ID>" --output my_song.mp3
```

### Tool 2 — BPM Detector

```bash
musicprod detect-bpm path/to/audio.mp3
```

### Tool 3 — Audio Format Converter

```bash
musicprod convert-format input.wav --to mp3
musicprod convert-format input.flac --to wav --output result.wav
```

### Tool 4 — Audio Trimmer

```bash
musicprod trim-audio input.mp3 --start 0:30 --end 1:45
musicprod trim-audio input.mp3 --start 10 --end 90 --output trimmed.mp3
```

### Tool 5 — Metadata Editor

```bash
# View tags
musicprod edit-metadata view path/to/file.mp3

# Set tags
musicprod edit-metadata set path/to/file.mp3 --title "My Song" --artist "DJ Example" --album "Demo"
```

### Tool 6 — Audio Normalizer

```bash
musicprod normalize-audio track.mp3
musicprod normalize-audio track.mp3 --target-dbfs -9.0 --output loud.mp3
```

### Tool 7 — Pitch Shifter

```bash
musicprod shift-pitch track.mp3 --semitones 2
musicprod shift-pitch track.mp3 --semitones -3 --output lower.mp3
```

### Tool 8 — Audio Splitter

```bash
musicprod split-audio long.mp3 --chunk-duration 30
musicprod split-audio long.mp3 --chunk-duration 60 --output-dir ./chunks
```

### Tool 9 — Audio Merger

```bash
musicprod merge-audio part1.mp3 part2.mp3 part3.mp3 --output full.mp3
```

### Tool 10 — Waveform Plotter

```bash
musicprod plot-waveform track.mp3
musicprod plot-waveform track.mp3 --width 16 --height 5 --output wave.png
```

---

## Running the Tests

```bash
# Install with dev dependencies (if you haven't already)
pip install -e ".[dev]"

# Run all tests with verbose output
pytest -v

# Run tests for a single tool
pytest tests/test_youtube_to_mp3.py -v
pytest tests/test_bpm_detector.py -v
pytest tests/test_format_converter.py -v
pytest tests/test_audio_trimmer.py -v
pytest tests/test_metadata_editor.py -v
pytest tests/test_audio_normalizer.py -v
pytest tests/test_pitch_shifter.py -v
pytest tests/test_audio_splitter.py -v
pytest tests/test_audio_merger.py -v
pytest tests/test_waveform_plotter.py -v
```

Tests run without a real internet connection or audio files — all external calls are mocked.

## Project Structure

```
musicprod/
├── musicprod/
│   ├── __init__.py
│   ├── cli.py                    ← Click CLI entry point (all 10 tools + hub)
│   ├── hub.py                    ← Tkinter graphical hub
│   └── tools/
│       ├── __init__.py
│       ├── youtube_to_mp3.py     ← Tool 1
│       ├── bpm_detector.py       ← Tool 2
│       ├── format_converter.py   ← Tool 3
│       ├── audio_trimmer.py      ← Tool 4
│       ├── metadata_editor.py    ← Tool 5
│       ├── audio_normalizer.py   ← Tool 6
│       ├── pitch_shifter.py      ← Tool 7
│       ├── audio_splitter.py     ← Tool 8
│       ├── audio_merger.py       ← Tool 9
│       └── waveform_plotter.py   ← Tool 10
├── tests/
├── requirements.txt
└── pyproject.toml
```

