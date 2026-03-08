"""Tool 10 — Waveform Plotter.

Generates a dark-themed waveform PNG image of an audio file using librosa
and matplotlib.

Enhancements over the basic version:
* **Spectrogram mode** — renders a mel spectrogram instead of a raw waveform.
  The spectrogram displays frequency content over time (logarithmic frequency
  axis), which is more useful for music analysis and matches what professional
  DAWs show in their timeline views.
* **RMS envelope overlay** — when enabled, draws a smoothed RMS energy curve
  on top of the waveform plot so loudness dynamics are immediately visible.
"""

from __future__ import annotations

from pathlib import Path


def plot_waveform(
    input_path: str,
    output_path: str | None = None,
    width: int = 12,
    height: int = 4,
    mode: str = "waveform",
    show_rms: bool = False,
) -> Path:
    """Generate a waveform or spectrogram image for *input_path*.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    output_path:
        Optional destination path.  Defaults to ``<stem>_waveform.png``
        or ``<stem>_spectrogram.png`` depending on *mode*.
    width:
        Figure width in inches (default: 12).
    height:
        Figure height in inches (default: 4).
    mode:
        Plot type.  One of:

        * ``"waveform"`` *(default)* — time-domain amplitude waveform.
        * ``"spectrogram"`` — mel spectrogram (frequency vs time,
          amplitude encoded as colour).
    show_rms:
        When ``True`` and *mode* is ``"waveform"``, overlay the smoothed
        RMS energy envelope as a bright line on top of the waveform
        (default: ``False``).

    Returns
    -------
    Path
        Path to the saved PNG image.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If *width* or *height* are not positive, or *mode* is unknown.
    RuntimeError
        If librosa or matplotlib fails.
    """
    import numpy as np
    import librosa  # lazy import
    import matplotlib  # lazy import
    matplotlib.use("Agg")  # non-interactive, file-only backend
    import matplotlib.pyplot as plt

    if width <= 0 or height <= 0:
        raise ValueError(f"width and height must be positive, got {width}×{height}")
    if mode not in ("waveform", "spectrogram"):
        raise ValueError(f"mode must be 'waveform' or 'spectrogram', got {mode!r}")

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        suffix = "spectrogram" if mode == "spectrogram" else "waveform"
        dest = src.with_name(f"{src.stem}_{suffix}.png")

    # Dark theme colours
    dark_bg = "#121212"
    accent = "#1DB954"   # Spotify green

    try:
        y, sr = librosa.load(str(src), sr=None, mono=True)

        fig, ax = plt.subplots(figsize=(width, height))
        ax.set_facecolor(dark_bg)
        fig.patch.set_facecolor(dark_bg)

        if mode == "spectrogram":
            # Mel spectrogram — log-scaled dB display
            S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
            S_db = librosa.power_to_db(S, ref=np.max)
            img = librosa.display.specshow(
                S_db,
                sr=sr,
                x_axis="time",
                y_axis="mel",
                ax=ax,
                cmap="magma",
            )
            cbar = fig.colorbar(img, ax=ax, format="%+2.0f dB")
            cbar.ax.yaxis.set_tick_params(color="white")
            plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")
            ax.set_title(f"{src.stem} — Mel Spectrogram")
        else:
            # Waveform
            times = librosa.times_like(y, sr=sr)
            ax.plot(times, y, linewidth=0.5, color=accent, alpha=0.8)
            ax.fill_between(times, y, alpha=0.25, color=accent)

            if show_rms:
                # Smoothed RMS envelope
                hop = 512
                rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop)[0]
                rms_times = librosa.frames_to_time(
                    np.arange(len(rms)), sr=sr, hop_length=hop
                )
                ax.plot(rms_times, rms, linewidth=1.5, color="#FFD700",
                        alpha=0.9, label="RMS")
                ax.plot(rms_times, -rms, linewidth=1.5, color="#FFD700", alpha=0.9)
                ax.legend(loc="upper right", facecolor="#333333", labelcolor="white",
                          framealpha=0.8)

            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Amplitude")
            ax.set_title(src.stem)

        # Uniform dark styling
        for item in (ax.xaxis.label, ax.yaxis.label, ax.title):
            item.set_color("white")
        ax.tick_params(colors="white")
        for spine in ax.spines.values():
            spine.set_color("#333333")

        fig.tight_layout()
        fig.savefig(str(dest), dpi=150, bbox_inches="tight")
        plt.close(fig)
    except (FileNotFoundError, ValueError):
        raise
    except Exception as exc:
        raise RuntimeError(f"Waveform plotting failed: {exc}") from exc

    return dest
