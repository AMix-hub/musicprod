"""Tool 22 — Vocal Auto-Tune (Advanced).

Professional-grade pitch correction for vocal recordings.

Key features
------------
* **Extended scale library** — major, minor (natural), dorian, phrygian,
  lydian, mixolydian, harmonic minor, melodic minor, pentatonic major/minor,
  blues, whole-tone, diminished, and chromatic.
* **Per-frame pitch correction** — PYIN analyses every hop rather than just
  the segment median, giving much finer control.
* **Retune speed** — IIR-smoothed correction envelope: ``0`` = instant
  (classic "robotic" T-Pain effect); higher values let the pitch glide
  naturally towards the target, matching how Auto-Tune Pro's Retune Speed
  knob works.
* **Transpose** — fixed semitone offset applied on top of the scale
  correction (handy for key-changes without re-exporting).
* **Humanize** — adds gentle, randomised pitch variation so the correction
  does not sound mechanical (amount 0–1 maps to ±0–25 cents of jitter).
* **Formant shift** — independently stretches the spectral envelope in the
  frequency domain so the "voice size" changes without touching the pitch
  (positive = brighter/smaller; negative = darker/larger).
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Scale helpers
# ---------------------------------------------------------------------------

_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Flat-spelling → sharp-spelling aliases
_FLAT_MAP: dict[str, str] = {
    "Db": "C#", "Eb": "D#", "Fb": "E", "Gb": "F#",
    "Ab": "G#", "Bb": "A#", "Cb": "B",
}

# Interval sets for every supported mode (semitones above root)
_SCALE_INTERVALS: dict[str, tuple[int, ...]] = {
    "major":           (0, 2, 4, 5, 7, 9, 11),
    "minor":           (0, 2, 3, 5, 7, 8, 10),   # natural minor
    "dorian":          (0, 2, 3, 5, 7, 9, 10),
    "phrygian":        (0, 1, 3, 5, 7, 8, 10),
    "lydian":          (0, 2, 4, 6, 7, 9, 11),
    "mixolydian":      (0, 2, 4, 5, 7, 9, 10),
    "harmonicminor":   (0, 2, 3, 5, 7, 8, 11),
    "melodicminor":    (0, 2, 3, 5, 7, 9, 11),
    "pentatonic":      (0, 2, 4, 7, 9),           # pentatonic major
    "pentaminor":      (0, 3, 5, 7, 10),          # pentatonic minor
    "blues":           (0, 3, 5, 6, 7, 10),
    "wholetone":       (0, 2, 4, 6, 8, 10),
    "diminished":      (0, 2, 3, 5, 6, 8, 9, 11),
}

# Friendly aliases that map to the canonical key above
_MODE_ALIASES: dict[str, str] = {
    "maj":              "major",
    "min":              "minor",
    "naturalminor":     "minor",
    "harmonic":         "harmonicminor",
    "harmonic minor":   "harmonicminor",
    "melodic":          "melodicminor",
    "melodic minor":    "melodicminor",
    "pentatonicmajor":  "pentatonic",
    "pentatonic major": "pentatonic",
    "pentatonic minor": "pentaminor",
    "whole tone":       "wholetone",
    "whole-tone":       "wholetone",
    "dim":              "diminished",
    "mixo":             "mixolydian",
    "phryg":            "phrygian",
    "lydian dominant":  "mixolydian",
}


def _normalise_mode(raw: str) -> str:
    """Map an arbitrary mode spelling to a canonical key in *_SCALE_INTERVALS*."""
    clean = raw.lower().replace("_", "").replace("-", "")
    if clean in _SCALE_INTERVALS:
        return clean
    if clean in _MODE_ALIASES:
        return _MODE_ALIASES[clean]
    # Try prefix matching (e.g. "maj" → "major")
    for alias, canon in _MODE_ALIASES.items():
        if clean.startswith(alias.replace(" ", "").replace("-", "")):
            return canon
    raise ValueError(
        f"Unknown mode {raw!r}. Supported modes: "
        + ", ".join(sorted(_SCALE_INTERVALS))
        + " (and common aliases such as 'harmonic minor', 'pentatonic major')."
    )


def _parse_scale(scale: str) -> list[int]:
    """Return the sorted pitch-class semitones (0–11) for *scale*.

    Accepted formats (case-insensitive):
        ``"chromatic"``                    — all 12 semitones
        ``"major"`` / ``"minor"``          — C major / C minor
        ``"C major"`` / ``"A minor"``
        ``"F# major"`` / ``"Bb minor"``
        ``"C dorian"`` / ``"D phrygian"``
        ``"G mixolydian"`` / ``"B lydian"``
        ``"A harmonic minor"`` / ``"D melodic minor"``
        ``"E pentatonic"`` / ``"A pentaminor"``
        ``"A blues"`` / ``"C whole tone"`` / ``"B diminished"``

    Raises
    ------
    ValueError
        If the root note or mode cannot be recognised.
    """
    scale = scale.strip()
    low = scale.lower()

    if low == "chromatic":
        return list(range(12))

    parts = scale.split(None, 1)  # split on first whitespace only

    if len(parts) == 1:
        root_str, mode_raw = "C", parts[0]
    else:
        root_str, mode_raw = parts[0], parts[1]

    canon_root = root_str.capitalize()
    canon_root = _FLAT_MAP.get(canon_root, canon_root)
    if canon_root not in _NOTES:
        raise ValueError(
            f"Unknown root note {root_str!r}. "
            f"Use one of: {', '.join(_NOTES)} (or flat equivalents such as Bb, Eb)."
        )
    root = _NOTES.index(canon_root)
    mode_key = _normalise_mode(mode_raw)
    intervals = _SCALE_INTERVALS[mode_key]
    return [(root + iv) % 12 for iv in intervals]


def _nearest_scale_midi(midi: float, scale_pcs: list[int]) -> float:
    """Return the MIDI pitch of the nearest note in *scale_pcs* to *midi*."""
    import numpy as np

    octave = int(midi) // 12
    # Span ±1 octave around the detected pitch to handle edge cases
    candidates = [
        (octave + oct_off) * 12 + pc
        for oct_off in (-1, 0, 1)
        for pc in scale_pcs
    ]
    arr = np.array(candidates, dtype=float)
    return float(arr[np.argmin(np.abs(arr - midi))])


def _apply_formant_shift(y: "np.ndarray", sr: int, shift_semitones: float) -> "np.ndarray":
    """Shift the spectral envelope (formants) by *shift_semitones* independently of pitch.

    Uses STFT-based spectral resampling: the magnitude spectrum of each
    frame is interpolated along the frequency axis by a factor of
    ``2**(shift_semitones/12)`` while the original phase is preserved.
    Positive values → brighter / smaller voice; negative → darker / larger.
    """
    import numpy as np
    import librosa

    if abs(shift_semitones) < 0.01:
        return y

    shift_factor = 2.0 ** (shift_semitones / 12.0)
    n_fft = 2048
    hop = 512

    D = librosa.stft(y, n_fft=n_fft, hop_length=hop)
    mag = np.abs(D)
    phase = np.angle(D)
    n_bins = D.shape[0]

    # Resample the magnitude spectrum along the frequency axis
    src_freqs = np.arange(n_bins, dtype=float)
    tgt_freqs = src_freqs / shift_factor  # where in the original spectrum to sample

    mag_shifted = np.zeros_like(mag)
    in_range = (tgt_freqs >= 0) & (tgt_freqs <= n_bins - 1)
    lo = np.floor(tgt_freqs[in_range]).astype(int)
    hi = np.minimum(lo + 1, n_bins - 1)
    frac = tgt_freqs[in_range] - lo

    # Vectorised linear interpolation across all time frames
    mag_shifted[in_range, :] = (
        mag[lo, :] * (1 - frac[:, np.newaxis])
        + mag[hi, :] * frac[:, np.newaxis]
    )

    D_shifted = mag_shifted * np.exp(1j * phase)
    return librosa.istft(D_shifted, hop_length=hop, length=len(y))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

# Output formats that soundfile can write natively
_SF_WRITE_FORMATS = {".wav", ".flac", ".ogg", ".aiff", ".aif"}


def autotune_vocals(
    input_path: str,
    scale: str = "chromatic",
    correction_strength: float = 1.0,
    retune_speed: float = 0.0,
    formant_shift: float = 0.0,
    transpose: float = 0.0,
    humanize: float = 0.0,
    output_path: str | None = None,
) -> Path:
    """Apply professional-grade auto-tune pitch correction to a vocal recording.

    Per-frame PYIN pitch tracking with IIR-smoothed correction gives results
    comparable to commercial pitch-correction plug-ins.

    Parameters
    ----------
    input_path:
        Path to the source audio file (MP3, WAV, FLAC, OGG, etc.).
    scale:
        Target musical scale.  Supported formats::

            "chromatic"        "C major"       "A minor"
            "F# dorian"        "D phrygian"    "G lydian"
            "B mixolydian"     "E harmonic minor"
            "C melodic minor"  "A pentatonic"  "A pentaminor"
            "A blues"          "C whole tone"  "B diminished"

        Omitting a root note defaults to **C** (e.g. ``"major"``).
        Flat notation is accepted (``"Bb minor"`` = ``"A# minor"``).
        Default: ``"chromatic"`` (snaps to the nearest semitone).
    correction_strength:
        How strongly to snap towards the target note.
        ``1.0`` = full correction (classic auto-tune effect).
        ``0.0`` = no correction (pass-through).
        Values between 0 and 1 produce a subtle / natural effect.
        Must be in the range [0.0, 1.0].
    retune_speed:
        Time constant (in milliseconds) of the pitch-correction envelope.
        ``0.0`` = instant snap (robotic "T-Pain" effect).
        ``50.0`` – ``200.0`` ms → natural-sounding glide into the target note,
        similar to Auto-Tune Pro's *Retune Speed* knob.
        Must be >= 0.
    formant_shift:
        Semitones to independently shift the spectral envelope (formants)
        without affecting the corrected pitch.
        ``0.0`` = no formant change (default).
        Positive values → brighter / perceived-smaller voice.
        Negative values → darker / perceived-larger voice.
    transpose:
        Fixed pitch offset in semitones applied after scale correction.
        Useful for key-shifting a fully corrected vocal without re-exporting.
        Default: ``0.0`` (no transposition).
    humanize:
        Amount of randomised pitch jitter (0.0–1.0) added on top of the
        smoothed correction to avoid an overly mechanical sound.
        ``0.0`` = no jitter.  ``1.0`` ≈ ±25 cents of random variation per
        frame.  Values around ``0.3`` simulate natural human imprecision.
        Must be in the range [0.0, 1.0].
    output_path:
        Optional destination path.  Defaults to
        ``<stem>_autotuned.<ext>``.  MP3 output falls back to ``.wav``
        because soundfile cannot write MP3.

    Returns
    -------
    Path
        Path to the pitch-corrected audio file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If *scale* cannot be parsed, or any parameter is outside its
        valid range.
    RuntimeError
        If audio processing fails.
    """
    import numpy as np
    import librosa          # lazy import — heavy dependency
    import soundfile as sf  # lazy import

    # ---- parameter validation ------------------------------------------------
    if not 0.0 <= correction_strength <= 1.0:
        raise ValueError(
            f"correction_strength must be between 0.0 and 1.0, "
            f"got {correction_strength}"
        )
    if retune_speed < 0.0:
        raise ValueError(
            f"retune_speed must be >= 0.0 ms, got {retune_speed}"
        )
    if not 0.0 <= humanize <= 1.0:
        raise ValueError(
            f"humanize must be between 0.0 and 1.0, got {humanize}"
        )

    scale_pcs = _parse_scale(scale)  # raises ValueError on bad input

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    if output_path:
        dest = Path(output_path).expanduser().resolve()
    else:
        dest = src.with_name(f"{src.stem}_autotuned{src.suffix}")

    if not dest.suffix or dest.suffix.lower() not in _SF_WRITE_FORMATS:
        dest = dest.with_suffix(".wav")

    try:
        y, sr = librosa.load(str(src), sr=None, mono=True)

        if len(y) == 0:
            sf.write(str(dest), y, sr)
            return dest

        hop_length = 512

        # PYIN: probabilistic pitch estimator, robust for sustained vocals
        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=float(librosa.note_to_hz("C2")),
            fmax=float(librosa.note_to_hz("C7")),
            sr=sr,
            hop_length=hop_length,
        )

        n_frames = len(f0)

        # ------------------------------------------------------------------
        # Per-frame correction calculation
        # For each voiced frame: compute the raw correction in semitones.
        # Unvoiced frames get 0 (unless transpose is set).
        # ------------------------------------------------------------------
        rng = np.random.default_rng(seed=42)  # reproducible humanize
        frame_corrections = np.zeros(n_frames, dtype=float)

        for idx in range(n_frames):
            if voiced_flag[idx] and not np.isnan(f0[idx]) and f0[idx] > 0:
                detected_midi = float(librosa.hz_to_midi(f0[idx]))
                target_midi = _nearest_scale_midi(detected_midi, scale_pcs)
                raw_shift = (target_midi - detected_midi) * correction_strength

                # Humanize: ±(humanize * 0.25) semitones of Gaussian jitter
                if humanize > 0.0:
                    raw_shift += float(rng.normal(0.0, humanize * 0.25))

                frame_corrections[idx] = raw_shift + transpose
            else:
                # Unvoiced: only apply transpose if set
                frame_corrections[idx] = transpose if transpose else 0.0

        # ------------------------------------------------------------------
        # Retune speed: IIR low-pass smoothing of the correction envelope.
        # retune_speed=0 → α=0 → instant (no smoothing).
        # ------------------------------------------------------------------
        if retune_speed > 0.0:
            frame_dur_s = hop_length / sr
            tau = retune_speed / 1000.0  # ms → s
            alpha = float(np.exp(-frame_dur_s / tau))
            smoothed = np.zeros(n_frames, dtype=float)
            for idx in range(n_frames):
                prev = smoothed[idx - 1] if idx > 0 else 0.0
                smoothed[idx] = alpha * prev + (1.0 - alpha) * frame_corrections[idx]
            frame_corrections = smoothed

        # ------------------------------------------------------------------
        # Apply pitch correction: group consecutive voiced frames with
        # similar shift, process each mini-segment, crossfade boundaries.
        # ------------------------------------------------------------------
        y_out = y.copy()
        crossfade_len = min(hop_length, 256)
        crossfade_win = np.linspace(0.0, 1.0, crossfade_len)

        i = 0
        while i < n_frames:
            # Skip fully unvoiced frames that need no shift
            if not voiced_flag[i] and abs(frame_corrections[i]) < 0.01:
                i += 1
                continue

            # Skip voiced frames where the smoothed correction is negligible
            if abs(frame_corrections[i]) < 0.01:
                i += 1
                continue

            # Collect a run of frames with similar correction (±0.15 st)
            seg_start_frame = i
            ref_shift = frame_corrections[i]
            while (
                i < n_frames
                and abs(frame_corrections[i] - ref_shift) < 0.15
                and (voiced_flag[i] or abs(frame_corrections[i]) >= 0.01)
            ):
                i += 1
            seg_end_frame = i

            start_sample = seg_start_frame * hop_length
            end_sample = min(seg_end_frame * hop_length, len(y))
            if end_sample <= start_sample:
                continue

            segment = y[start_sample:end_sample]
            # Use the mean shift over the segment frames for accuracy
            seg_shift = float(np.mean(frame_corrections[seg_start_frame:seg_end_frame]))

            if abs(seg_shift) < 0.01:
                continue

            try:
                corrected = librosa.effects.pitch_shift(
                    segment, sr=sr, n_steps=seg_shift
                )
                # Match original segment length
                if len(corrected) < len(segment):
                    corrected = np.pad(corrected, (0, len(segment) - len(corrected)))
                else:
                    corrected = corrected[: len(segment)]

                # Crossfade at the leading edge to avoid clicks
                cf = min(crossfade_len, len(corrected), end_sample - start_sample)
                if cf > 0 and start_sample > 0:
                    fade_in = crossfade_win[:cf]
                    fade_out = 1.0 - fade_in
                    y_out[start_sample: start_sample + cf] = (
                        fade_out * y_out[start_sample: start_sample + cf]
                        + fade_in * corrected[:cf]
                    )
                    y_out[start_sample + cf: end_sample] = corrected[cf:]
                else:
                    y_out[start_sample:end_sample] = corrected
            except Exception:
                pass  # leave segment unmodified on failure

        # ------------------------------------------------------------------
        # Optional formant shift (spectral envelope modification)
        # ------------------------------------------------------------------
        if abs(formant_shift) >= 0.01:
            y_out = _apply_formant_shift(y_out, sr, formant_shift)

        sf.write(str(dest), y_out, sr)

    except (FileNotFoundError, ValueError):
        raise
    except Exception as exc:
        raise RuntimeError(f"Auto-tune failed: {exc}") from exc

    return dest
