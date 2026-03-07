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
pip install -e ".[dev]"
pytest
```

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
