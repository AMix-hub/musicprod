"""Tool 23 — Stem Splitter (Advanced).

Separates an audio file into up to four independent stems using a
multi-stage signal-processing pipeline:

1. **HPSS** (Harmonic/Percussive Source Separation via median-filtering on the
   magnitude spectrogram) isolates percussive transients (drums, cymbals) from
   tonal content (vocals, bass, instruments).

2. **Frequency-band split** of the harmonic layer extracts:

   * **Drums** — the percussive HPSS component.
   * **Bass** — all harmonic energy below *bass_cutoff* Hz (default 300 Hz).
   * **Vocals / melody** — on *stereo* material the mid channel (L+R)/2
     captures centre-panned sources (lead vocals, kick sub, solo instrument);
     on *mono* material the full harmonic-above-cutoff layer is used.
   * **Other** — any harmonic energy not attributed to bass or vocals
     (wide-panned instruments, guitars, pads, etc.).

3. Each stem is saved as an independent WAV file in a user-supplied directory
   (or a ``<source_stem>_stems/`` subdirectory created beside the source).

Because the approach is entirely signal-processing-based (HPSS + spectral
masking + M/S extraction), it runs without a GPU and on any machine that can
run Python + librosa.  Quality is comparable to single-source separation tools
on clean studio recordings.

Supported stem keys (any subset may be requested):
    ``"drums"``, ``"bass"``, ``"vocals"``, ``"other"``
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

# Default stems produced when the caller does not restrict the list
_ALL_STEMS = ("drums", "bass", "vocals", "other")
_VALID_STEMS = frozenset(_ALL_STEMS)


def split_stems(
    input_path: str,
    stems: Sequence[str] | None = None,
    output_dir: str | None = None,
    bass_cutoff: float = 300.0,
    hpss_margin: float = 3.0,
    hpss_kernel_size: int = 31,
) -> dict[str, Path]:
    """Separate *input_path* into independent stem files.

    Parameters
    ----------
    input_path:
        Path to the source audio file (MP3, WAV, FLAC, OGG, etc.).
    stems:
        Sequence of stem names to produce.  Any subset of
        ``["drums", "bass", "vocals", "other"]``.  ``None`` produces all four.
    output_dir:
        Directory where stem files are written.  Defaults to
        ``<source_stem>_stems/`` next to the source file.
    bass_cutoff:
        Frequency in Hz below which harmonic content is classified as
        **bass** (default: 300 Hz).  Typical values: 200–400 Hz.
    hpss_margin:
        Margin parameter for :func:`librosa.decompose.hpss`.  Higher values
        produce a crisper separation but may bleed more artefacts (default 3).
    hpss_kernel_size:
        Median-filter kernel size (in frequency bins and time frames) for HPSS
        (default: 31).  Larger values → smoother separation.

    Returns
    -------
    dict[str, Path]
        Mapping of stem name → path to the written WAV file.

    Raises
    ------
    FileNotFoundError
        If *input_path* does not exist.
    ValueError
        If *stems* contains an unknown stem name, or a parameter is invalid.
    RuntimeError
        If audio loading or processing fails.
    """
    import numpy as np
    import librosa
    import soundfile as sf

    # ---- validation ----------------------------------------------------------
    if stems is None:
        stems = list(_ALL_STEMS)
    else:
        stems = list(stems)

    unknown = set(stems) - _VALID_STEMS
    if unknown:
        raise ValueError(
            f"Unknown stem(s): {unknown!r}.  "
            f"Valid stems: {sorted(_VALID_STEMS)}"
        )
    if not stems:
        raise ValueError("stems must contain at least one stem name.")

    if bass_cutoff <= 0:
        raise ValueError(f"bass_cutoff must be > 0 Hz, got {bass_cutoff}")
    if hpss_margin < 1:
        raise ValueError(f"hpss_margin must be >= 1, got {hpss_margin}")
    if hpss_kernel_size < 1:
        raise ValueError(f"hpss_kernel_size must be >= 1, got {hpss_kernel_size}")

    src = Path(input_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Input file not found: {src}")

    if output_dir:
        out_dir = Path(output_dir).expanduser().resolve()
    else:
        out_dir = src.parent / f"{src.stem}_stems"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Load — keep native sample rate; load stereo when available
        y_full, sr = librosa.load(str(src), sr=None, mono=False)

        # Determine whether source is stereo
        is_stereo = y_full.ndim == 2 and y_full.shape[0] == 2

        # Work on a mono mixdown for STFT-based separation
        if is_stereo:
            y_mono = librosa.to_mono(y_full)  # (T,)
            y_left = y_full[0]
            y_right = y_full[1]
            y_mid = (y_left + y_right) * 0.5   # mid (centre-panned)
            y_side = (y_left - y_right) * 0.5  # side (wide-panned)
        else:
            if y_full.ndim == 2:
                y_mono = librosa.to_mono(y_full)
            else:
                y_mono = y_full
            y_mid = y_mono
            y_side = np.zeros_like(y_mono)

        n_fft = 2048
        hop_length = 512

        # ------------------------------------------------------------------
        # HPSS — split mono into harmonic + percussive soft masks
        # ------------------------------------------------------------------
        D_mono = librosa.stft(y_mono, n_fft=n_fft, hop_length=hop_length)
        mag_mono = np.abs(D_mono)
        phase_mono = np.angle(D_mono)

        H_mask_norm, P_mask_norm = librosa.decompose.hpss(
            mag_mono,
            kernel_size=hpss_kernel_size,
            margin=hpss_margin,
            power=2.0,
            mask=True,
        )

        # Reconstruct mono percussive waveform (drums)
        perc_mono = librosa.istft(
            P_mask_norm * mag_mono * np.exp(1j * phase_mono),
            hop_length=hop_length,
            length=len(y_mono),
        )

        # ------------------------------------------------------------------
        # Frequency-band masks for bass / upper harmonic split
        # ------------------------------------------------------------------
        freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
        bass_bins = freqs < bass_cutoff            # True for bass frequencies
        upper_bins = ~bass_bins                    # True for mid/high freqs

        # Project bass/upper masks onto harmonic STFT
        bass_freq_mask = bass_bins[:, np.newaxis].astype(float)   # (F, 1)
        upper_freq_mask = upper_bins[:, np.newaxis].astype(float)

        # Harmonic STFT weighted by frequency-band masks
        D_harm = H_mask_norm * mag_mono * np.exp(1j * phase_mono)
        harm_bass = librosa.istft(
            D_harm * bass_freq_mask,
            hop_length=hop_length,
            length=len(y_mono),
        )
        harm_upper = librosa.istft(
            D_harm * upper_freq_mask,
            hop_length=hop_length,
            length=len(y_mono),
        )

        # ------------------------------------------------------------------
        # Mid/Side split for vocals vs other (stereo only)
        # For mono, vocals = upper harmonic, other = zeros
        # ------------------------------------------------------------------
        if is_stereo:
            # Apply the same harmonic-upper mask to the mid/side channels
            D_mid = librosa.stft(y_mid, n_fft=n_fft, hop_length=hop_length)
            D_side = librosa.stft(y_side, n_fft=n_fft, hop_length=hop_length)

            # Vocals: mid channel × upper-harmonic mask
            vocals_mid = librosa.istft(
                D_mid * H_mask_norm * upper_freq_mask,
                hop_length=hop_length,
                length=len(y_mono),
            )
            # Other: side channel × upper-harmonic mask
            other_side = librosa.istft(
                D_side * H_mask_norm * upper_freq_mask,
                hop_length=hop_length,
                length=len(y_mono),
            )
            # Reconstruct to stereo: vocals centred, other wide-panned
            vocals_stereo = np.stack([vocals_mid, vocals_mid], axis=0)
            other_stereo = np.stack(
                [other_side, -other_side], axis=0
            )  # L = side, R = -side
        else:
            vocals_mid = harm_upper
            other_side = np.zeros_like(y_mono)

        # ------------------------------------------------------------------
        # Helper: reconstruct stereo stem from mono component
        # (for drums and bass we use the mono signal on both channels)
        # ------------------------------------------------------------------
        def _to_output(mono_sig: "np.ndarray") -> "np.ndarray":
            """Return (T,) for mono source or (T, 2) for stereo source."""
            if is_stereo:
                stereo = np.stack([mono_sig, mono_sig], axis=0)  # (2, T)
                return stereo.T  # (T, 2) for soundfile
            return mono_sig

        # ------------------------------------------------------------------
        # Write stems
        # ------------------------------------------------------------------
        output: dict[str, Path] = {}
        stem_name = src.stem

        stem_data: dict[str, np.ndarray] = {}
        if "drums" in stems:
            stem_data["drums"] = _to_output(perc_mono)
        if "bass" in stems:
            stem_data["bass"] = _to_output(harm_bass)
        if "vocals" in stems:
            if is_stereo:
                stem_data["vocals"] = vocals_stereo.T  # (T, 2)
            else:
                stem_data["vocals"] = vocals_mid
        if "other" in stems:
            if is_stereo:
                stem_data["other"] = other_stereo.T  # (T, 2)
            else:
                stem_data["other"] = other_side

        for stem_key, data in stem_data.items():
            dest = out_dir / f"{stem_name}_{stem_key}.wav"
            sf.write(str(dest), data, sr)
            output[stem_key] = dest

    except (FileNotFoundError, ValueError):
        raise
    except Exception as exc:
        raise RuntimeError(f"Stem splitting failed: {exc}") from exc

    return output
