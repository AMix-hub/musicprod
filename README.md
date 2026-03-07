# MusicProd Tools 🎵

A collection of command-line tools for music production, built in Python.

## Top 5 Music Production Tools

We work through these tools one by one — each solves a concrete problem in the music production workflow:

| # | Tool | Description |
|---|------|-------------|
| 1 | **YouTube → MP3** | Download audio from YouTube links and save as MP3 files |
| 2 | **BPM Detector** | Analyse an audio file and detect its tempo (BPM) |
| 3 | **Audio Format Converter** | Convert between audio formats (MP3, WAV, FLAC, OGG, AAC …) |
| 4 | **Audio Trimmer** | Trim an audio file to a specific start/end timestamp |
| 5 | **Metadata Editor** | View and edit ID3/audio metadata tags (artist, title, album …) |

---

## Quick Start

Follow these steps to go from a fresh clone to running commands in under five minutes.

### 1. Install FFmpeg

FFmpeg is required by the format-converter and audio-trimmer tools.

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

You should see the five tools listed:

```
Usage: musicprod [OPTIONS] COMMAND [ARGS]...

  MusicProd — music production tools.

  Top 5 tools:
    1. youtube-to-mp3   Download audio from YouTube as MP3
    2. detect-bpm       Detect the BPM/tempo of an audio file
    3. convert-format   Convert audio between formats
    4. trim-audio       Trim an audio file to start/end timestamps
    5. edit-metadata    View or edit audio file metadata tags
```

### 5. Run the test suite

```bash
pytest -v
```

All tests run without needing real audio files or a live internet connection — everything is mocked.

---

## Requirements

- Python 3.9+
- [FFmpeg](https://ffmpeg.org/download.html) installed and on your `PATH`

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
```

Tests run without a real internet connection or audio files — all external calls are mocked.

## Project Structure

```
musicprod/
├── musicprod/
│   ├── __init__.py
│   ├── cli.py                 ← Click CLI entry point
│   └── tools/
│       ├── __init__.py
│       ├── youtube_to_mp3.py  ← Tool 1
│       ├── bpm_detector.py    ← Tool 2
│       ├── format_converter.py← Tool 3
│       ├── audio_trimmer.py   ← Tool 4
│       └── metadata_editor.py ← Tool 5
├── tests/
├── requirements.txt
└── pyproject.toml
```
