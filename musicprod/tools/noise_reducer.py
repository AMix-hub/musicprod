"""Tool 11 — Noise Reducer.

Reduces background noise in an audio file using either classic spectral
subtraction or a Wiener filter (softer, more musical result).

Spectral subtraction estimates a noise profile from a quiet section of the
audio and subtracts its magnitude spectrum from the full signal.  The Wiener
filter variant applies an optimal MMSE gain function that is much gentler and
preserves transients better — the technique used in most professional
noise-reduction plug-ins.
"""

from __future__ import annotations

from pathlib import Path

_SF_WRITE_FORMATS = {".wav", ".flac", ".ogg", ".aiff", ".aif"}


def reduce_noise(
    input_path: str,
    output_path: str | None = None,
    noise_duration: float = 0.5,
    strength: float = 1.0,
    method: str = "wiener",
    spectral_floor: float = 0.05,
) -> Path:
    """Reduce background noise in *input_path*.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    output_path:
        Optional destination path.  Defaults to ``<stem>_denoised.<ext>``.
    noise_duration:
        Seconds from the start of the file used to estimate the noise
        profile (default: 0.5 s).  Must be > 0.
    strength:
        Noise suppression strength multiplier (default: 1.0, range 0–3).
        Higher values remove more noise but may introduce artefacts.
    method:
        Noise-reduction algorithm to use:

        * ``"wiener"`` *(default)* — MMSE Wiener filter; produces the
          most musical, artefact-free results.  Preferred for vocals and
          instruments.
        * ``"subtract"`` — classic spectral subtraction; faster and more
          aggressive.  Best for heavy background noise.
    spectral_floor:
        Minimum gain floor applied to each frequency bin (default: 0.05).
        Prevents over-subtraction and "musical noise" artefacts common in
        aggressive spectral subtraction.  Must be in [0.0, 1.0].

    Returns
    -------
    Path
        Path to the denoised audio file.

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
    import librosa  # lazy import
    import soundfile as sf  # lazy import

    if noise_duration <= 0:
        raise ValueError(f"noise_duration must be > 0, got {noise_duration}")
    if strength < 0:
        raise ValueError(f"strength must be >= 0, got {strength}")
    if method not in ("wiener", "subtract"):
        raise ValueError(
            f"method must be 'wiener' or 'subtract', got {method!r}"
        )
    if not 0.0 <= spectral_floor <= 1.0:
        raise ValueError(
            f"spectral_floor must be between 0.0 and 1.0, got {spectral_floor}"
        )

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_denoised{src.suffix}")

    if not dest.suffix or dest.suffix.lower() not in _SF_WRITE_FORMATS:
        dest = dest.with_suffix(".wav")

    try:
        y, sr = librosa.load(str(src), sr=None, mono=False)

        # Handle multi-channel: process each channel independently
        if y.ndim == 1:
            y = y[np.newaxis, :]  # (1, T)
        channels = y

        noise_samples = int(noise_duration * sr)
        n_fft = 2048
        hop_length = 512

        denoised_channels = []
        for ch in channels:
            noise_clip = ch[:noise_samples] if len(ch) > noise_samples else ch
            noise_stft = librosa.stft(noise_clip, n_fft=n_fft, hop_length=hop_length)
            # Noise power spectral density (PSD) — averaged over time
            noise_psd = np.mean(np.abs(noise_stft) ** 2, axis=1, keepdims=True)

            stft = librosa.stft(ch, n_fft=n_fft, hop_length=hop_length)
            mag = np.abs(stft)
            phase = np.angle(stft)
            signal_psd = mag ** 2

            if method == "wiener":
                # MMSE Wiener gain: H = max(1 - (strength * N) / S, floor)
                # This is the "parametric Wiener filter" used in speech enhancement.
                noise_est = strength * noise_psd
                wiener_gain = np.maximum(
                    1.0 - noise_est / np.maximum(signal_psd, 1e-10),
                    spectral_floor,
                )
                reduced_mag = wiener_gain * mag
            else:
                # Classic spectral subtraction with floor
                noise_mag = np.sqrt(noise_psd)
                reduced_mag = np.maximum(
                    mag - strength * noise_mag,
                    spectral_floor * mag,
                )

            stft_denoised = reduced_mag * np.exp(1j * phase)
            ch_out = librosa.istft(stft_denoised, hop_length=hop_length, length=len(ch))
            denoised_channels.append(ch_out)

        result = np.stack(denoised_channels, axis=0)
        if result.shape[0] == 1:
            result = result[0]  # back to mono (1-D)
        else:
            result = result.T  # soundfile expects (T, channels)

        sf.write(str(dest), result, sr)
    except (FileNotFoundError, ValueError):
        raise
    except Exception as exc:
        raise RuntimeError(f"Noise reduction failed: {exc}") from exc

    return dest
