"""Tool 7 — Pitch Shifter.

Shifts the pitch of an audio file by a given number of semitones using
librosa for processing and soundfile for output.

Enhancements over the basic version:
* **Stereo support** — each channel is processed independently so stereo
  recordings are no longer silently downmixed to mono.
* **Formant preservation** flag — when enabled, applies a complementary
  spectral envelope correction after pitch-shifting to keep the voice
  character intact (avoids the "chipmunk" artefact on large shifts).
"""

from __future__ import annotations

from pathlib import Path

_SF_WRITE_FORMATS = {".wav", ".flac", ".ogg", ".aiff", ".aif"}


def shift_pitch(
    input_path: str,
    semitones: float,
    preserve_formants: bool = False,
    output_path: str | None = None,
) -> Path:
    """Shift the pitch of *input_path* by *semitones*.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    semitones:
        Number of semitones to shift.  Positive values raise the pitch;
        negative values lower it.
    preserve_formants:
        When ``True``, apply a spectral envelope correction after pitch
        shifting to reduce the "chipmunk" / "monster" artefact on large
        shifts (default: ``False``).
    output_path:
        Optional destination path.  Defaults to ``<stem>_pitched.<ext>``.
        MP3 sources fall back to ``.wav`` output.

    Returns
    -------
    Path
        Path to the pitch-shifted file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    RuntimeError
        If librosa or soundfile fails.
    """
    import numpy as np
    import librosa  # lazy import
    import soundfile as sf  # lazy import

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_pitched{src.suffix}")

    if not dest.suffix or dest.suffix.lower() not in _SF_WRITE_FORMATS:
        dest = dest.with_suffix(".wav")

    try:
        y, sr = librosa.load(str(src), sr=None, mono=False)

        if y.ndim == 1:
            # Mono
            shifted = librosa.effects.pitch_shift(y=y, sr=sr, n_steps=semitones)
            if preserve_formants:
                shifted = _correct_formants(y, shifted, sr, semitones)
            result = shifted
        else:
            # Stereo / multi-channel: process each channel independently
            channels_out = []
            for ch in y:
                ch_shifted = librosa.effects.pitch_shift(y=ch, sr=sr, n_steps=semitones)
                if preserve_formants:
                    ch_shifted = _correct_formants(ch, ch_shifted, sr, semitones)
                channels_out.append(ch_shifted)
            result = np.stack(channels_out, axis=0).T  # (T, channels)

        sf.write(str(dest), result, sr)
    except (FileNotFoundError, ValueError):
        raise
    except Exception as exc:
        raise RuntimeError(f"Pitch shift failed: {exc}") from exc

    return dest


def _correct_formants(
    original: "np.ndarray",
    shifted: "np.ndarray",
    sr: int,
    shift_semitones: float,
) -> "np.ndarray":
    """Apply a spectral envelope correction to counteract formant shift.

    After pitch-shifting by *shift_semitones*, the spectral envelope
    (formants) has also been shifted by the same amount.  This function
    re-scales the magnitude spectrum of *shifted* so that its envelope
    approximates the envelope of *original*, restoring the voice character.
    """
    import numpy as np
    import librosa

    n_fft = 2048
    hop = 512

    D_orig = librosa.stft(original, n_fft=n_fft, hop_length=hop)
    D_shifted = librosa.stft(shifted, n_fft=n_fft, hop_length=hop)

    # Compute smoothed spectral envelopes via moving average over frequency bins
    window = max(1, n_fft // 64)
    env_orig = _smooth_envelope(np.abs(D_orig), window)
    env_shifted = _smooth_envelope(np.abs(D_shifted), window)

    # Avoid division by zero; apply correction ratio
    ratio = np.where(env_shifted > 1e-8, env_orig / env_shifted, 1.0)
    D_corrected = D_shifted * ratio

    return librosa.istft(D_corrected, hop_length=hop, length=len(original))


def _smooth_envelope(mag: "np.ndarray", window: int) -> "np.ndarray":
    """Compute a moving-average spectral envelope along the frequency axis."""
    import numpy as np
    from numpy.lib.stride_tricks import sliding_window_view

    pad = window // 2
    padded = np.pad(mag, ((pad, pad), (0, 0)), mode="edge")
    # Efficient moving average using cumulative sum
    cumsum = np.cumsum(padded, axis=0)
    return (cumsum[window:] - cumsum[:-window]) / window
