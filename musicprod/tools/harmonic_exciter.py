"""Tool 25 — Harmonic Exciter (Professional-Grade).

Adds harmonic content to an audio signal to restore perceived brightness,
warmth, and presence — particularly useful for:

* Acoustic recordings that sound dull or lacking sparkle.
* Mastering chains where you want subtle analogue colouration.
* Vocal processing to add "air" or "body".
* Bass lines that need more definition and punch.

Algorithm overview
------------------
1. **Band-split** — the signal is split into a low-shelf (sub/bass) region
   and a high-shelf (presence/air) region using two complementary Butterworth
   filters, so that the saturation can be applied in a frequency-selective way.

2. **Saturation** — one of three industry-standard transfer functions is
   applied to the selected frequency band(s):

   * ``"tube"`` — soft-knee even-harmonic saturation that emulates the
     smooth compression of a triode valve.  Transfer function:
     ``y = x / (1 + |x|)^(1 – drive)``.  Produces a warm, rounded character.

   * ``"tape"`` — gentle hysteresis-like saturation modelled as
     ``y = tanh(drive_gain · x) / tanh(drive_gain)``, matching the magnetic
     saturation curve of analogue tape.  Adds subtle compression, warmth, and
     high-frequency softening.

   * ``"transistor"`` — asymmetric hard-knee clipping that introduces
     predominantly odd-order harmonics, characteristic of silicon transistor
     circuits.  Transfer function: soft-clip on the positive half, harder
     clip on the negative half.  Adds edge and aggression.

3. **Blend** — the saturated signal is mixed with the clean (dry) signal via a
   linear crossfade controlled by the ``blend`` parameter (0 = fully dry,
   1 = fully wet).

Parameters
----------
drive:
    Saturation amount, 0.0–1.0.  0 = no additional harmonics; 1 = maximum
    saturation/drive.  Values 0.2–0.5 are typical for transparent processing.
blend:
    Dry/wet mix ratio, 0.0–1.0.  0 = original signal only; 1 = fully
    processed signal.  Default: 0.5.
mode:
    Saturation character: ``"tube"`` (even harmonics, warm), ``"tape"``
    (smooth compression), or ``"transistor"`` (odd harmonics, edge).
freq_band:
    Frequency range to saturate:

    * ``"full"`` — apply saturation to the entire spectrum.
    * ``"highs"`` — apply only to frequencies above ``band_cutoff`` Hz
      (default 3 kHz), preserving the bass untouched.  Best for adding air.
    * ``"lows"`` — apply only below ``band_cutoff`` Hz.  Best for bass warmth.
band_cutoff:
    Cross-over frequency in Hz for ``freq_band="highs"`` or ``"lows"``
    (default: 3000 Hz).
output_path:
    Optional destination path; defaults to ``<stem>_excited.<ext>``.
"""

from __future__ import annotations

from pathlib import Path

_VALID_MODES = frozenset({"tube", "tape", "transistor"})
_VALID_BANDS = frozenset({"full", "highs", "lows"})
_SF_WRITE_FORMATS = {".wav", ".flac", ".ogg", ".aiff", ".aif"}


# ---------------------------------------------------------------------------
# Saturation transfer functions (vectorised for numpy arrays)
# ---------------------------------------------------------------------------

def _saturate_tube(x: "np.ndarray", drive: float) -> "np.ndarray":
    """Valve/tube soft-even-harmonic saturation.

    Approximates the curvature of a triode characteristic.  Higher *drive*
    increases the amount of harmonics generated.
    """
    import numpy as np
    # Normalise by peak so drive is relative rather than absolute
    peak = np.max(np.abs(x)) + 1e-9
    xn = x / peak
    # Soft-clip: y = x / (1 + |x|^(1 + drive*2))
    exponent = 1.0 + drive * 2.0
    yn = xn / (1.0 + np.abs(xn) ** exponent)
    # Re-scale to original peak amplitude
    return yn * peak


def _saturate_tape(x: "np.ndarray", drive: float) -> "np.ndarray":
    """Magnetic tape saturation via scaled tanh.

    The gain before the tanh is 1 + drive * 4, giving increasing saturation
    from 1× (linear at drive=0) to 5× (heavy at drive=1).
    """
    import numpy as np
    gain = 1.0 + drive * 4.0
    peak = np.max(np.abs(x)) + 1e-9
    xn = x / peak
    denom = float(np.tanh(gain))
    yn = np.tanh(gain * xn) / (denom if denom > 1e-9 else 1.0)
    return yn * peak


def _saturate_transistor(x: "np.ndarray", drive: float) -> "np.ndarray":
    """Asymmetric transistor-style hard/soft clip.

    Positive half: standard soft clip (generates lower odd harmonics).
    Negative half: slightly harder clip (asymmetric → even harmonics too).
    Mimics bipolar-transistor distortion pedals.
    """
    import numpy as np
    gain = 1.0 + drive * 5.0
    peak = np.max(np.abs(x)) + 1e-9
    xn = x * gain / peak

    # Positive half: soft tanh
    pos = np.where(xn > 0, np.tanh(xn), 0.0)
    # Negative half: harder — clips at –0.8 then tanh
    neg = np.where(xn < 0, np.tanh(xn * 1.3), 0.0)
    yn = pos + neg
    # Normalise output to peak to match input level
    out_peak = np.max(np.abs(yn)) + 1e-9
    return (yn / out_peak) * peak


_SATURATORS = {
    "tube":        _saturate_tube,
    "tape":        _saturate_tape,
    "transistor":  _saturate_transistor,
}


# ---------------------------------------------------------------------------
# Butterworth band-split helpers
# ---------------------------------------------------------------------------

def _butter_split(
    y: "np.ndarray",
    sr: int,
    cutoff: float,
    band: str,
) -> tuple["np.ndarray", "np.ndarray"]:
    """Return (band_signal, remainder_signal) for the chosen *band*.

    ``band="highs"`` → apply filter to high-shelf; remainder = low-shelf.
    ``band="lows"``  → apply filter to low-shelf; remainder = high-shelf.
    """
    from scipy.signal import butter, sosfiltfilt

    nyq = sr * 0.5
    norm_cutoff = min(cutoff / nyq, 0.999)

    if band == "highs":
        sos = butter(4, norm_cutoff, btype="high", output="sos")
        band_sig = sosfiltfilt(sos, y)
        remainder = y - band_sig
    else:  # "lows"
        sos = butter(4, norm_cutoff, btype="low", output="sos")
        band_sig = sosfiltfilt(sos, y)
        remainder = y - band_sig

    return band_sig, remainder


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def excite(
    input_path: str,
    drive: float = 0.3,
    blend: float = 0.5,
    mode: str = "tube",
    freq_band: str = "highs",
    band_cutoff: float = 3000.0,
    output_path: str | None = None,
) -> Path:
    """Apply harmonic excitation to *input_path*.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    drive:
        Saturation drive amount 0.0–1.0 (default: 0.3).
    blend:
        Dry/wet mix 0.0–1.0 (default: 0.5).
    mode:
        Saturation character: ``"tube"`` | ``"tape"`` | ``"transistor"``.
    freq_band:
        Which frequency range to saturate: ``"full"`` | ``"highs"`` | ``"lows"``.
    band_cutoff:
        Cross-over frequency in Hz when ``freq_band`` is ``"highs"`` or
        ``"lows"`` (default: 3000 Hz).
    output_path:
        Optional destination path.  Defaults to ``<stem>_excited.<ext>``.
        MP3 inputs fall back to ``.wav``.

    Returns
    -------
    Path
        Path to the excited audio file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If any parameter is invalid.
    RuntimeError
        If audio processing fails.
    """
    import numpy as np
    import librosa
    import soundfile as sf

    # ---- validation ----------------------------------------------------------
    if not 0.0 <= drive <= 1.0:
        raise ValueError(f"drive must be between 0.0 and 1.0, got {drive}")
    if not 0.0 <= blend <= 1.0:
        raise ValueError(f"blend must be between 0.0 and 1.0, got {blend}")
    if mode not in _VALID_MODES:
        raise ValueError(
            f"mode must be one of {sorted(_VALID_MODES)}, got {mode!r}"
        )
    if freq_band not in _VALID_BANDS:
        raise ValueError(
            f"freq_band must be one of {sorted(_VALID_BANDS)}, got {freq_band!r}"
        )
    if band_cutoff <= 0:
        raise ValueError(f"band_cutoff must be > 0, got {band_cutoff}")

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_excited{src.suffix}")

    if not dest.suffix or dest.suffix.lower() not in _SF_WRITE_FORMATS:
        dest = dest.with_suffix(".wav")

    try:
        y, sr = librosa.load(str(src), sr=None, mono=False)

        is_stereo = y.ndim == 2 and y.shape[0] == 2

        def _process_channel(ch: "np.ndarray") -> "np.ndarray":
            """Apply excitation to a single channel array."""
            saturate = _SATURATORS[mode]

            if freq_band == "full":
                wet = saturate(ch, drive)
            else:
                band_sig, remainder = _butter_split(ch, sr, band_cutoff, freq_band)
                excited_band = saturate(band_sig, drive)
                wet = excited_band + remainder

            # Blend dry / wet
            return ch * (1.0 - blend) + wet * blend

        if is_stereo:
            left = _process_channel(y[0])
            right = _process_channel(y[1])
            result = np.stack([left, right], axis=0).T  # (T, 2)
        else:
            if y.ndim == 2:
                mono = librosa.to_mono(y)
            else:
                mono = y
            result = _process_channel(mono)

        # Prevent clipping — normalise to just below 0 dBFS if needed
        peak = np.max(np.abs(result))
        if peak > 0.99:
            result = result * (0.99 / peak)

        sf.write(str(dest), result, sr)

    except (FileNotFoundError, ValueError):
        raise
    except Exception as exc:
        raise RuntimeError(f"Harmonic excitation failed: {exc}") from exc

    return dest
