"""Tool 11 — Noise Reducer.

Reduces background noise in an audio file using spectral subtraction
(estimates noise profile from the first 500 ms then subtracts it).
"""

from __future__ import annotations

from pathlib import Path


def reduce_noise(
    input_path: str,
    output_path: str | None = None,
    noise_duration: float = 0.5,
    strength: float = 1.0,
) -> Path:
    """Reduce background noise in *input_path* via spectral subtraction.

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
        Subtraction strength multiplier (default: 1.0, range 0–3).
        Higher values remove more noise but may introduce artefacts.

    Returns
    -------
    Path
        Path to the denoised audio file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If *noise_duration* or *strength* is invalid.
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

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_denoised{src.suffix}")

    # soundfile infers the output format from the extension.
    # Ensure the destination always has a supported extension; fall back
    # to .wav when the source has no extension or an unsupported one (e.g. .mp3).
    _SF_WRITE_FORMATS = {".wav", ".flac", ".ogg", ".aiff", ".aif"}
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
            # Estimate noise magnitude spectrum from the first noise_duration seconds
            noise_clip = ch[:noise_samples] if len(ch) > noise_samples else ch
            noise_stft = librosa.stft(noise_clip, n_fft=n_fft, hop_length=hop_length)
            noise_mag = np.mean(np.abs(noise_stft), axis=1, keepdims=True)

            # Full signal STFT
            stft = librosa.stft(ch, n_fft=n_fft, hop_length=hop_length)
            mag = np.abs(stft)
            phase = np.angle(stft)

            # Spectral subtraction
            reduced_mag = np.maximum(mag - strength * noise_mag, 0)
            stft_denoised = reduced_mag * np.exp(1j * phase)

            ch_out = librosa.istft(stft_denoised, hop_length=hop_length, length=len(ch))
            denoised_channels.append(ch_out)

        result = np.stack(denoised_channels, axis=0)
        if result.shape[0] == 1:
            result = result[0]  # back to mono (1-D)
        else:
            result = result.T  # soundfile expects (T, channels)

        sf.write(str(dest), result, sr)
    except Exception as exc:
        raise RuntimeError(f"Noise reduction failed: {exc}") from exc

    return dest
