"""Tool 16 — Reverb Effect.

Adds a studio-quality algorithmic reverb to an audio file.

The reverb is modelled using a multi-tap delay network with exponentially
decaying reflections — the same principle used in classic hardware reverb
units (e.g. Lexicon 224) and most software reverb plug-ins.

Extra controls compared to the basic version:
* **dry/wet mix** — blend the original ("dry") signal with the reverb
  ("wet") for precise depth control.
* **pre_delay_ms** — initial silence before the first reflection, used to
  place the reverb tail behind transients (standard feature in all pro
  reverbs).
* **room_size** preset shorthand that automatically sets reflections and
  decay to match ``"small"``, ``"medium"``, or ``"large"`` rooms.
"""

from __future__ import annotations

from pathlib import Path

_ROOM_PRESETS: dict[str, dict[str, object]] = {
    "small":  {"reflections": 4,  "decay": 0.25, "delay_ms": 20},
    "medium": {"reflections": 7,  "decay": 0.40, "delay_ms": 60},
    "large":  {"reflections": 12, "decay": 0.55, "delay_ms": 100},
}


def add_reverb(
    input_path: str,
    delay_ms: int = 80,
    decay: float = 0.4,
    reflections: int = 5,
    wet_level: float = 0.3,
    pre_delay_ms: int = 0,
    room_size: str | None = None,
    output_path: str | None = None,
) -> Path:
    """Add a reverb effect to *input_path*.

    A room-reverb simulation is produced by overlaying progressively
    quieter, delayed copies of the source signal and blending the result
    back with the dry signal at the requested *wet_level*.

    Parameters
    ----------
    input_path:
        Path to the source audio file.
    delay_ms:
        Delay between successive reflections in milliseconds (default: 80).
        Must be > 0.
    decay:
        Volume reduction factor per reflection, between 0 and 1
        (default: 0.4).  Lower = darker, more distant reverb.
    reflections:
        Number of reflected copies to add (default: 5, range 1–20).
    wet_level:
        Dry/wet mix for the reverb tail (default: 0.3).
        ``0.0`` = fully dry (no reverb); ``1.0`` = fully wet.
        Must be in [0.0, 1.0].
    pre_delay_ms:
        Milliseconds of silence inserted before the first reflection
        (default: 0).  Values of 10–30 ms help separate the direct
        sound from the reverb, improving clarity on vocals.
        Must be >= 0.
    room_size:
        Optional preset that overrides *delay_ms*, *decay*, and
        *reflections*.  One of ``"small"``, ``"medium"``, ``"large"``.
        When set, the individual parameters are ignored.
    output_path:
        Optional destination path.  Defaults to ``<stem>_reverb.<ext>``.

    Returns
    -------
    Path
        Path to the processed audio file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If parameters are out of range.
    RuntimeError
        If pydub / FFmpeg fails.
    """
    from pydub import AudioSegment  # lazy import

    # Apply room_size preset overrides first
    if room_size is not None:
        room_size = room_size.lower()
        if room_size not in _ROOM_PRESETS:
            raise ValueError(
                f"room_size must be one of {list(_ROOM_PRESETS)}, got {room_size!r}"
            )
        preset = _ROOM_PRESETS[room_size]
        reflections = int(preset["reflections"])
        decay = float(preset["decay"])
        delay_ms = int(preset["delay_ms"])

    if delay_ms <= 0:
        raise ValueError(f"delay_ms must be > 0, got {delay_ms}")
    if not 0 < decay < 1:
        raise ValueError(f"decay must be between 0 and 1 (exclusive), got {decay}")
    if not 1 <= reflections <= 20:
        raise ValueError(f"reflections must be between 1 and 20, got {reflections}")
    if not 0.0 <= wet_level <= 1.0:
        raise ValueError(f"wet_level must be between 0.0 and 1.0, got {wet_level}")
    if pre_delay_ms < 0:
        raise ValueError(f"pre_delay_ms must be >= 0, got {pre_delay_ms}")

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    try:
        audio = AudioSegment.from_file(str(src))
    except Exception as exc:
        raise RuntimeError(f"Failed to load audio: {exc}") from exc

    # Build wet signal by layering echoes
    total_delay = delay_ms * reflections + pre_delay_ms
    wet = AudioSegment.silent(
        duration=len(audio) + total_delay,
        frame_rate=audio.frame_rate,
    ).set_channels(audio.channels)

    for i in range(1, reflections + 1):
        gain_db = 20 * _log10_safe(decay ** i)
        offset = pre_delay_ms + delay_ms * i
        reflection = audio - abs(gain_db)
        wet = wet.overlay(reflection, position=offset)

    # Extend dry signal to match wet length
    dry_extended = audio + AudioSegment.silent(
        duration=total_delay,
        frame_rate=audio.frame_rate,
    ).set_channels(audio.channels)

    # Dry/wet blend: apply dB gain to wet to achieve wet_level mix
    if wet_level <= 0.0:
        mixed = dry_extended
    elif wet_level >= 1.0:
        mixed = wet
    else:
        # Convert wet_level (0–1 amplitude ratio) to dB attenuation for wet
        wet_db = 20 * _log10_safe(wet_level)
        dry_db = 20 * _log10_safe(1.0 - wet_level)
        mixed = dry_extended.apply_gain(dry_db).overlay(wet.apply_gain(wet_db))

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_reverb{src.suffix}")

    if not dest.suffix:
        dest = dest.with_suffix(src.suffix or ".mp3")

    try:
        fmt = dest.suffix.lstrip(".") or "mp3"
        mixed.export(str(dest), format=fmt)
    except Exception as exc:
        raise RuntimeError(f"Failed to export reverb audio: {exc}") from exc

    return dest


def _log10_safe(x: float) -> float:
    import math
    return math.log10(max(x, 1e-9))
