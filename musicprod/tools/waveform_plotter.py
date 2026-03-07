"""Tool 10 — Waveform Plotter.

Generates a waveform PNG image of an audio file using librosa and matplotlib.
"""

from __future__ import annotations

from pathlib import Path


def plot_waveform(
    input_path: str,
    output_path: str | None = None,
    width: int = 12,
    height: int = 4,
) -> Path:
    """Generate a waveform image for *input_path* and save it as a PNG.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    output_path:
        Optional destination path.  Defaults to ``<stem>_waveform.png``.
    width:
        Figure width in inches (default: 12).
    height:
        Figure height in inches (default: 4).

    Returns
    -------
    Path
        Path to the saved PNG image.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If *width* or *height* are not positive.
    RuntimeError
        If librosa or matplotlib fails.
    """
    import librosa  # lazy import
    import matplotlib  # lazy import
    matplotlib.use("Agg")  # non-interactive, file-only backend
    import matplotlib.pyplot as plt

    if width <= 0 or height <= 0:
        raise ValueError(f"width and height must be positive, got {width}×{height}")

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_waveform.png")

    try:
        y, sr = librosa.load(str(src), sr=None, mono=True)
        times = librosa.times_like(y, sr=sr)

        fig, ax = plt.subplots(figsize=(width, height))
        ax.plot(times, y, linewidth=0.5, color="#1DB954")
        ax.fill_between(times, y, alpha=0.3, color="#1DB954")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Amplitude")
        ax.set_title(src.stem)

        # Dark theme styling
        dark_bg = "#121212"
        ax.set_facecolor(dark_bg)
        fig.patch.set_facecolor(dark_bg)
        for item in (ax.xaxis.label, ax.yaxis.label, ax.title):
            item.set_color("white")
        ax.tick_params(colors="white")
        for spine in ax.spines.values():
            spine.set_color("#333333")

        fig.tight_layout()
        fig.savefig(str(dest), dpi=150, bbox_inches="tight")
        plt.close(fig)
    except Exception as exc:
        raise RuntimeError(f"Waveform plotting failed: {exc}") from exc

    return dest
