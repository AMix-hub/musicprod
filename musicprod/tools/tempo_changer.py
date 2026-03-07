"""Tool 15 — Tempo Changer.

Changes the tempo (speed) of an audio file without altering the pitch,
using librosa's time-stretching algorithm.
"""

from __future__ import annotations

from pathlib import Path


def change_tempo(
    input_path: str,
    rate: float = 1.0,
    output_path: str | None = None,
) -> Path:
    """Time-stretch *input_path* by *rate* without changing pitch.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    rate:
        Speed multiplier (default: 1.0 = unchanged).
        ``2.0`` doubles the speed; ``0.5`` halves it.
        Must be in the range (0.1, 10.0].
    output_path:
        Optional destination path.  Defaults to ``<stem>_tempo.<ext>``.

    Returns
    -------
    Path
        Path to the processed audio file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If *rate* is out of the allowed range.
    RuntimeError
        If audio processing fails.
    """
    import numpy as np
    import librosa  # lazy import
    import soundfile as sf  # lazy import

    if not 0.1 <= rate <= 10.0:
        raise ValueError(f"rate must be between 0.1 and 10.0, got {rate}")

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_tempo{src.suffix}")

    # soundfile infers the output format from the extension.
    # Ensure the destination always has a supported extension; fall back
    # to .wav when the source has no extension or an unsupported one (e.g. .mp3).
    _SF_WRITE_FORMATS = {".wav", ".flac", ".ogg", ".aiff", ".aif"}
    if not dest.suffix or dest.suffix.lower() not in _SF_WRITE_FORMATS:
        dest = dest.with_suffix(".wav")

    try:
        y, sr = librosa.load(str(src), sr=None, mono=False)

        if y.ndim == 1:
            stretched = librosa.effects.time_stretch(y, rate=rate)
        else:
            # Process each channel independently and re-stack
            channels = [librosa.effects.time_stretch(y[i], rate=rate) for i in range(y.shape[0])]
            stretched = np.stack(channels, axis=0).T  # (T, channels)

        sf.write(str(dest), stretched, sr)
    except Exception as exc:
        raise RuntimeError(f"Tempo change failed: {exc}") from exc

    return dest
