"""Tool 7 — Pitch Shifter.

Shifts the pitch of an audio file by a given number of semitones using
librosa for processing and pydub for audio I/O.
"""

from __future__ import annotations

from pathlib import Path


def shift_pitch(
    input_path: str,
    semitones: float,
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
    output_path:
        Optional destination path.  Defaults to ``<stem>_pitched.<ext>``.

    Returns
    -------
    Path
        Path to the pitch-shifted file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    RuntimeError
        If librosa or pydub fails.
    """
    import numpy as np  # librosa dependency — always available
    import librosa  # lazy import

    from pydub import AudioSegment  # lazy import

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_pitched{src.suffix}")

    try:
        y, sr = librosa.load(str(src), sr=None, mono=True)
        shifted = librosa.effects.pitch_shift(y=y, sr=sr, n_steps=semitones)

        # Clamp to valid float range and convert to 16-bit PCM for pydub
        shifted = np.clip(shifted, -1.0, 1.0)
        pcm = (shifted * 32767).astype(np.int16)

        audio_seg = AudioSegment(
            pcm.tobytes(),
            frame_rate=sr,
            sample_width=2,  # 2 bytes = int16
            channels=1,
        )

        fmt = dest.suffix.lstrip(".") or "mp3"
        audio_seg.export(str(dest), format=fmt)
    except Exception as exc:
        raise RuntimeError(f"Pitch shift failed: {exc}") from exc

    return dest
