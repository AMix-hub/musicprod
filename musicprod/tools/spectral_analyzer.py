"""Tool 24 — Spectral Analyzer (Professional-Grade).

Generates a comprehensive multi-panel spectral analysis image of an audio file,
combining four complementary visualisations on a single professional dark-themed
canvas:

1. **Mel Spectrogram** — frequency content over time mapped to the perceptual
   mel scale.  The most useful view for understanding timbre and energy
   distribution.  A ``hop_length``-aligned time axis and a Hz-labelled
   frequency axis make it easy to read back into physical time/frequency
   coordinates.

2. **Chroma Features** — 12-bin pitch-class energy (C, C#, D … B) projected
   from the constant-Q transform.  Shows which notes / harmonics are active
   and lets you read the key centre and chord movement at a glance.

3. **Spectral Centroid** — the "centre of mass" of the spectrum at each frame,
   plotted as a time-series overlay.  A rising centroid means the mix is
   getting brighter (more highs); a falling centroid means it is getting
   darker/warmer.

4. **RMS Energy** — root-mean-square amplitude envelope, a perceptual loudness
   proxy.  Useful for spotting the track's dynamic structure (intro, drop,
   chorus, etc.).

All four panels share a common time axis so you can line up events across
views.

Output: a PNG (or other matplotlib-supported format, detected from the file
extension) saved to *output_path* (default: ``<stem>_analysis.png``).
"""

from __future__ import annotations

from pathlib import Path


def analyze_spectrum(
    input_path: str,
    output_path: str | None = None,
    n_mels: int = 128,
    n_fft: int = 2048,
    hop_length: int = 512,
    fmin: float = 20.0,
    fmax: float | None = None,
    top_db: float = 80.0,
    width: int = 1400,
    height: int = 900,
) -> Path:
    """Analyse *input_path* and save a multi-panel spectral analysis image.

    Parameters
    ----------
    input_path:
        Path to the source audio file (MP3, WAV, FLAC, OGG, etc.).
    output_path:
        Destination image path.  Format is inferred from the extension
        (e.g. ``.png``, ``.jpg``, ``.pdf``).
        Defaults to ``<stem>_analysis.png``.
    n_mels:
        Number of mel frequency bands (default: 128).  Higher → more
        frequency resolution.  Common values: 64, 128, 256.
    n_fft:
        FFT window size in samples (default: 2048).  Larger windows give
        better frequency resolution at the cost of time resolution.
    hop_length:
        Number of samples between successive frames (default: 512).
        Smaller values produce a denser, higher time-resolution plot.
    fmin:
        Lowest frequency to display on the mel spectrogram (default: 20 Hz).
    fmax:
        Highest frequency to display (default: ``sr / 2``).
    top_db:
        Dynamic range (in dB) shown on the mel spectrogram.  Lower values
        compress the colour range; 80 dB is a good default.
    width:
        Output image width in pixels (default: 1400).
    height:
        Output image height in pixels (default: 900).

    Returns
    -------
    Path
        Path to the saved analysis image.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If any parameter is out of range.
    RuntimeError
        If audio loading or plot generation fails.
    """
    import numpy as np
    import librosa
    import matplotlib
    matplotlib.use("Agg")  # headless rendering
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec

    # ---- validation ----------------------------------------------------------
    if n_mels < 1:
        raise ValueError(f"n_mels must be >= 1, got {n_mels}")
    if n_fft < 1:
        raise ValueError(f"n_fft must be >= 1, got {n_fft}")
    if hop_length < 1:
        raise ValueError(f"hop_length must be >= 1, got {hop_length}")
    if fmin < 0:
        raise ValueError(f"fmin must be >= 0, got {fmin}")
    if top_db <= 0:
        raise ValueError(f"top_db must be > 0, got {top_db}")
    if width < 100:
        raise ValueError(f"width must be >= 100, got {width}")
    if height < 100:
        raise ValueError(f"height must be >= 100, got {height}")

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_analysis.png")

    try:
        y, sr = librosa.load(str(src), sr=None, mono=True)
        duration = librosa.get_duration(y=y, sr=sr)

        # ---- feature extraction ---------------------------------------------
        # 1. Mel spectrogram
        S_mel = librosa.feature.melspectrogram(
            y=y,
            sr=sr,
            n_fft=n_fft,
            hop_length=hop_length,
            n_mels=n_mels,
            fmin=fmin,
            fmax=fmax,
        )
        S_mel_db = librosa.power_to_db(S_mel, ref=np.max, top_db=top_db)

        # 2. Chroma (CQT-based, more robust than STFT chroma)
        chroma = librosa.feature.chroma_cqt(
            y=y,
            sr=sr,
            hop_length=hop_length,
        )

        # 3. Spectral centroid (Hz)
        centroid = librosa.feature.spectral_centroid(
            y=y,
            sr=sr,
            n_fft=n_fft,
            hop_length=hop_length,
        )[0]

        # 4. RMS energy
        rms = librosa.feature.rms(
            y=y,
            frame_length=n_fft,
            hop_length=hop_length,
        )[0]

        # Common time axis
        times = librosa.frames_to_time(
            np.arange(len(centroid)),
            sr=sr,
            hop_length=hop_length,
        )

        # ---- plotting -------------------------------------------------------
        dpi = 100
        fig_w = width / dpi
        fig_h = height / dpi

        # Dark professional theme
        plt.rcParams.update({
            "figure.facecolor": "#0d0d0d",
            "axes.facecolor":   "#141414",
            "axes.edgecolor":   "#444444",
            "axes.labelcolor":  "#dddddd",
            "xtick.color":      "#999999",
            "ytick.color":      "#999999",
            "text.color":       "#dddddd",
            "grid.color":       "#2a2a2a",
            "grid.linestyle":   "--",
            "grid.linewidth":   0.5,
        })

        fig = plt.figure(figsize=(fig_w, fig_h), dpi=dpi)
        fig.suptitle(
            f"Spectral Analysis — {src.name}  "
            f"({duration:.1f} s · {sr / 1000:.1f} kHz)",
            fontsize=13,
            color="#ff69b4",
            fontweight="bold",
            y=0.98,
        )

        gs = gridspec.GridSpec(
            4, 1,
            figure=fig,
            hspace=0.55,
            left=0.07, right=0.97,
            top=0.93, bottom=0.06,
            height_ratios=[3, 1.5, 1, 1],
        )

        # — Panel 1: Mel spectrogram —
        ax1 = fig.add_subplot(gs[0])
        img = librosa.display.specshow(
            S_mel_db,
            x_axis="time",
            y_axis="mel",
            sr=sr,
            hop_length=hop_length,
            fmin=fmin,
            fmax=fmax,
            cmap="magma",
            ax=ax1,
        )
        ax1.set_title("Mel Spectrogram (dBFS)", color="#ff69b4", fontsize=10)
        ax1.set_xlabel("")
        cbar1 = fig.colorbar(img, ax=ax1, format="%+2.0f dB", pad=0.01)
        cbar1.ax.yaxis.set_tick_params(color="#999999")
        plt.setp(cbar1.ax.yaxis.get_ticklabels(), color="#999999", fontsize=8)
        ax1.grid(True, alpha=0.3)

        # — Panel 2: Chroma —
        ax2 = fig.add_subplot(gs[1])
        note_names = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"]
        img2 = librosa.display.specshow(
            chroma,
            x_axis="time",
            y_axis="chroma",
            sr=sr,
            hop_length=hop_length,
            cmap="coolwarm",
            ax=ax2,
        )
        ax2.set_title("Chroma Features (pitch-class energy)", color="#7ecfff", fontsize=10)
        ax2.set_xlabel("")
        ax2.set_yticklabels(note_names, fontsize=7)
        cbar2 = fig.colorbar(img2, ax=ax2, pad=0.01)
        plt.setp(cbar2.ax.yaxis.get_ticklabels(), color="#999999", fontsize=8)
        ax2.grid(True, alpha=0.3)

        # — Panel 3: Spectral Centroid —
        ax3 = fig.add_subplot(gs[2])
        centroid_khz = centroid / 1000.0
        ax3.plot(times, centroid_khz, color="#ff69b4", linewidth=0.8, label="Centroid (kHz)")
        ax3.fill_between(times, centroid_khz, alpha=0.25, color="#ff69b4")
        ax3.set_title("Spectral Centroid", color="#ff69b4", fontsize=10)
        ax3.set_ylabel("kHz", fontsize=8)
        ax3.set_xlabel("")
        ax3.set_xlim(0, duration)
        ax3.set_ylim(bottom=0)
        ax3.grid(True, alpha=0.3)
        ax3.legend(fontsize=7, loc="upper right", framealpha=0.3)

        # — Panel 4: RMS Energy —
        ax4 = fig.add_subplot(gs[3])
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)
        ax4.plot(times, rms_db, color="#50fa7b", linewidth=0.8, label="RMS (dB)")
        ax4.fill_between(times, rms_db, rms_db.min(), alpha=0.25, color="#50fa7b")
        ax4.set_title("RMS Energy", color="#50fa7b", fontsize=10)
        ax4.set_ylabel("dBFS", fontsize=8)
        ax4.set_xlabel("Time (s)", fontsize=9)
        ax4.set_xlim(0, duration)
        ax4.grid(True, alpha=0.3)
        ax4.legend(fontsize=7, loc="upper right", framealpha=0.3)

        fig.savefig(str(dest), dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)

    except (FileNotFoundError, ValueError):
        raise
    except Exception as exc:
        raise RuntimeError(f"Spectral analysis failed: {exc}") from exc

    return dest
