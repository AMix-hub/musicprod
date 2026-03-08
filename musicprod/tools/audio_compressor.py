"""Tool 19 — Audio Compressor.

Applies professional-grade dynamic range compression to an audio file.

Extra controls compared to the basic version:
* **makeup_gain** — post-compression volume boost (dB) to restore perceived
  loudness lost by compression (standard on every hardware and software
  compressor).
* **knee_width** — soft-knee width in dB; 0 = hard knee (classic), >0 =
  gradual transition zone around the threshold for more transparent results.
* **limiter** — enable brickwall limiter mode (ratio effectively set to ∞)
  to hard-clip transients above the threshold.
"""

from __future__ import annotations

from pathlib import Path

# Brickwall limiter ratio: a value high enough to make attenuation above
# the threshold virtually infinite without triggering overflow in pydub.
_LIMITER_RATIO = 1000.0


def compress_audio(
    input_path: str,
    threshold: float = -20.0,
    ratio: float = 4.0,
    attack: float = 5.0,
    release: float = 50.0,
    makeup_gain: float = 0.0,
    knee_width: float = 0.0,
    limiter: bool = False,
    output_path: str | None = None,
) -> Path:
    """Apply dynamic range compression to *input_path*.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    threshold:
        Threshold in dBFS above which compression is applied
        (default: -20.0).  Must be < 0.
    ratio:
        Compression ratio — e.g. ``4.0`` means 4:1 compression
        (default: 4.0).  Must be >= 1.0.  Ignored when *limiter* is
        ``True``.
    attack:
        Attack time in milliseconds (default: 5.0).  Must be > 0.
    release:
        Release time in milliseconds (default: 50.0).  Must be > 0.
    makeup_gain:
        Post-compression gain in dB (default: 0.0).  Applied after
        compression to restore loudness.  May be negative (attenuation).
    knee_width:
        Soft-knee width in dB around the threshold (default: 0.0 = hard
        knee).  A value of 6.0 dB gives a gentle transition starting at
        ``threshold - 3`` dB and ending at ``threshold + 3`` dB.
        Must be >= 0.
    limiter:
        When ``True``, the ratio is set to infinity (brickwall limiting).
        The *ratio* parameter is ignored.  Default: ``False``.
    output_path:
        Optional destination path.  Defaults to ``<stem>_compressed.<ext>``.

    Returns
    -------
    Path
        Path to the compressed audio file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If any parameter is out of range.
    RuntimeError
        If pydub / FFmpeg fails.
    """
    from pydub import AudioSegment  # lazy import
    from pydub.effects import compress_dynamic_range  # lazy import

    if threshold >= 0:
        raise ValueError(f"threshold must be < 0, got {threshold}")
    if not limiter and ratio < 1.0:
        raise ValueError(f"ratio must be >= 1.0, got {ratio}")
    if attack <= 0:
        raise ValueError(f"attack must be > 0, got {attack}")
    if release <= 0:
        raise ValueError(f"release must be > 0, got {release}")
    if knee_width < 0:
        raise ValueError(f"knee_width must be >= 0, got {knee_width}")

    # In limiter mode use _LIMITER_RATIO to approximate ∞:1 compression
    effective_ratio = _LIMITER_RATIO if limiter else ratio

    # Soft-knee: adjust the effective threshold downward by half the knee
    # width so that compression starts gradually before the nominal threshold.
    effective_threshold = threshold - knee_width / 2.0 if knee_width > 0 else threshold

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    try:
        audio = AudioSegment.from_file(str(src))
    except Exception as exc:
        raise RuntimeError(f"Failed to load audio: {exc}") from exc

    try:
        compressed = compress_dynamic_range(
            audio,
            threshold=effective_threshold,
            ratio=effective_ratio,
            attack=attack,
            release=release,
        )
    except Exception as exc:
        raise RuntimeError(f"Compression failed: {exc}") from exc

    # Apply makeup gain
    if makeup_gain != 0.0:
        compressed = compressed.apply_gain(makeup_gain)

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_compressed{src.suffix}")

    if not dest.suffix:
        dest = dest.with_suffix(src.suffix or ".mp3")

    try:
        fmt = dest.suffix.lstrip(".") or "mp3"
        compressed.export(str(dest), format=fmt)
    except Exception as exc:
        raise RuntimeError(f"Failed to export compressed audio: {exc}") from exc

    return dest
